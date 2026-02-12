# Heart Rate Detection & Detailed Mode Implementation

This document explains how the project implements core heart rate calculation and the detailed mode outputs (HRV/AF/irregularity), with key function excerpts.

**Scope**
- Sampling and filtering: `app/src/main/java/com/health/monitor/features/heartrate/domain/HeartRateDetector.kt`
- Calculation engine and HRV/AF/irregularity: `app/src/main/java/com/health/monitor/features/heartrate/domain/HeartRateCalculationEngine.kt`
- Result model: `app/src/main/java/com/health/monitor/features/heartrate/domain/model/HeartRateResult.kt`
- Detailed mode and UI: `app/src/main/java/com/health/monitor/features/heartrate/ui/HeartRateViewModel.kt`, `app/src/main/java/com/health/monitor/features/heartrate/ui/HeartRateDetectionScreen.kt`

**Flow Overview**
1. Camera frames enter `HeartRateDetector.processVideoFrame`, which extracts the red channel, validates finger placement, filters the signal, and emits `PPGSample` values.
2. `HeartRateCalculationEngine.processSample` accumulates samples and triggers `calculateHeartRateFromSamples` once the required duration is reached.
3. The engine computes RR intervals, BPM, stability, confidence, signal quality, and derives HRV (SDNN/RMSSD) plus irregular risk metrics.
4. Results are surfaced via `HeartRateResult` into `HeartRateViewModel` state flows.
5. The UI renders HRV, AF risk, and irregularity details in detailed mode.

**Key Function: Sampling and Filtering**
File: `app/src/main/java/com/health/monitor/features/heartrate/domain/HeartRateDetector.kt`
```kotlin
fun processVideoFrame(bitmap: Bitmap): PPGSample {
    val timestamp = SystemClock.elapsedRealtimeNanos() / 1_000_000_000.0

    // Extract red channel value
    val redValue = extractRedChannelValue(bitmap)

    // Finger placement detection
    checkFingerPlacement(redValue)

    // Only process samples after finger placement
    if (!shouldCollectSamples) {
        return PPGSample(
            timestamp = timestamp,
            redChannelValue = redValue,
            filteredValue = 0.0,
            movingAverageValue = 0.0,
            bandPassFiltered = 0.0
        )
    }

    // Skip the first 1 second (30 samples) after finger placement
    sampleCountSinceStart++
    if (sampleCountSinceStart <= SKIP_INITIAL_SAMPLES) {
        return PPGSample(
            timestamp = timestamp,
            redChannelValue = redValue,
            filteredValue = 0.0,
            movingAverageValue = 0.0,
            bandPassFiltered = 0.0
        )
    }

    // Apply moving average filter
    val movingAverageValue = movingAverageFilter.filter(redValue)

    // Apply band-pass filter (0.5-4 Hz for heart rate)
    val bandPassFiltered = bandPassFilter.filter(redValue)

    // Create sample with all stages
    val sample = PPGSample(
        timestamp = timestamp,
        redChannelValue = redValue,
        filteredValue = bandPassFiltered,
        movingAverageValue = movingAverageValue,
        bandPassFiltered = bandPassFiltered
    )

    samples.add(sample)
    waveformData.add(bandPassFiltered.toFloat())

    // Feed calculation engine in real time
    calculationEngine.processSample(sample)

    return sample
}
```

**Key Function: Core Calculation Entry**
File: `app/src/main/java/com/health/monitor/features/heartrate/domain/HeartRateCalculationEngine.kt`
```kotlin
private fun calculateHeartRateFromSamples(samples: List<PPGSample>): HeartRateResult {
    if (samples.size <= (SAMPLE_RATE * 2).toInt()) {
        return HeartRateResult(
            averageBPM = 0.0,
            stability = 0.0,
            confidence = 0.0,
            timestamp = Date(),
            waveformData = emptyList(),
            peakCount = 0,
            signalQuality = 0.0
        )
    }

    val filteredValues = samples.map { it.bandPassFiltered }
    val smoothedValues = smoothSignal(filteredValues, SMOOTHING_WINDOW)
    val normalizedValues = detrendSignal(smoothedValues)

    val peaks = detectPeaks(normalizedValues, samples)

    val rawIntervals = computeIntervalsSeconds(peaks, samples)
    val intervals = filterIntervals(rawIntervals)
    val bpm = calculateBpmFromIntervals(intervals)

    val stability = calculateStabilityFromIntervals(intervals)
    val confidence = calculateConfidence(filteredValues, peaks, samples)
    val signalQuality = calculateSignalQuality(filteredValues)

    val hrvMetrics = calculateHrvMetrics(intervals)
    val irregularMetrics = calculateIrregularRisk(intervals, hrvMetrics)

    return HeartRateResult(
        averageBPM = bpm,
        stability = stability,
        confidence = confidence,
        timestamp = Date(),
        waveformData = filteredValues.map { it.toFloat() },
        peakCount = peaks.size,
        signalQuality = signalQuality,
        hrvSdnnMs = hrvMetrics?.sdnnMs,
        hrvRmssdMs = hrvMetrics?.rmssdMs,
        afRiskProbability = irregularMetrics?.afRiskProbability,
        irregularRiskLevel = irregularMetrics?.riskLevel,
        irregularPulseHint = irregularMetrics?.hint,
        detectionDurationSeconds = detectionDurationSeconds
    )
}
```

**Key Function: RR Intervals and HRV (SDNN/RMSSD)**
File: `app/src/main/java/com/health/monitor/features/heartrate/domain/HeartRateCalculationEngine.kt`
```kotlin
private fun computeIntervalsSeconds(peaks: List<Int>, samples: List<PPGSample>): List<Double> {
    if (peaks.size < 2) return emptyList()
    val intervals = mutableListOf<Double>()
    for (i in 1 until peaks.size) {
        val current = samples.getOrNull(peaks[i])?.timestamp ?: continue
        val previous = samples.getOrNull(peaks[i - 1])?.timestamp ?: continue
        val interval = current - previous
        // Filter unrealistic range (30-240 BPM)
        if (interval in 0.25..2.0) {
            intervals.add(interval)
        }
    }
    return intervals
}

private fun calculateHrvMetrics(intervalsSeconds: List<Double>): HrvMetrics? {
    if (intervalsSeconds.size < 3) return null
    val rrMs = intervalsSeconds.map { it * 1000.0 }
    val mean = rrMs.average()
    val variance = rrMs.map { (it - mean).pow(2) }.average()
    val sdnn = sqrt(variance)

    var diffSum = 0.0
    for (i in 1 until rrMs.size) {
        val diff = rrMs[i] - rrMs[i - 1]
        diffSum += diff * diff
    }
    val rmssd = sqrt(diffSum / (rrMs.size - 1).toDouble())
    return HrvMetrics(sdnnMs = sdnn, rmssdMs = rmssd, meanRrMs = mean)
}
```

**Key Function: AF Risk Probability and Irregular Risk**
File: `app/src/main/java/com/health/monitor/features/heartrate/domain/HeartRateCalculationEngine.kt`
```kotlin
private fun calculateIrregularRisk(
    intervalsSeconds: List<Double>,
    hrvMetrics: HrvMetrics?
): IrregularRiskMetrics? {
    if (intervalsSeconds.size < 3 || hrvMetrics == null) return null

    val meanRrMs = hrvMetrics.meanRrMs
    val sdnn = hrvMetrics.sdnnMs
    val rmssd = hrvMetrics.rmssdMs

    val cv = if (meanRrMs > 0) sdnn / meanRrMs else 0.0
    val rmssdRatio = if (meanRrMs > 0) rmssd / meanRrMs else 0.0

    fun normalize(value: Double, low: Double, high: Double): Double {
        if (high <= low) return 0.0
        return ((value - low) / (high - low)).coerceIn(0.0, 1.0)
    }

    val cvScore = normalize(cv, 0.08, 0.22)
    val rmssdScore = normalize(rmssdRatio, 0.12, 0.28)
    val irregularScore = (cvScore * 0.6 + rmssdScore * 0.4).coerceIn(0.0, 1.0)

    val riskLevel = when {
        irregularScore >= 0.66 -> "High"
        irregularScore >= 0.33 -> "Medium"
        else -> "Low"
    }

    val hint = when {
        irregularScore >= 0.66 ->
            "Nonspecific irregularity detected. Consider further evaluation."
        irregularScore >= 0.33 ->
            "Possible irregularity detected. Please monitor closely."
        else ->
            "No obvious irregularity detected."
    }

    return IrregularRiskMetrics(
        afRiskProbability = irregularScore,
        riskLevel = riskLevel,
        hint = hint
    )
}
```

**Key Function: Detailed Mode Duration and Data Binding**
File: `app/src/main/java/com/health/monitor/features/heartrate/ui/HeartRateViewModel.kt`
```kotlin
companion object {
    private const val STANDARD_DURATION_SECONDS = 20.0
    private const val DETAILED_DURATION_SECONDS = 60.0
    private const val WARMUP_SECONDS = 10.0
}

enum class HeartRateDetectionMode(val durationSeconds: Double) {
    STANDARD(STANDARD_DURATION_SECONDS),
    DETAILED(DETAILED_DURATION_SECONDS)
}

private fun handleDetectionResult(result: HeartRateResult) {
    _hrvSdnnMs.value = result.hrvSdnnMs
    _hrvRmssdMs.value = result.hrvRmssdMs
    _afRiskProbability.value = result.afRiskProbability
    _irregularRiskLevel.value = result.irregularRiskLevel
    _irregularPulseHint.value = result.irregularPulseHint
}
```

**Key Function: Detailed Mode UI**
File: `app/src/main/java/com/health/monitor/features/heartrate/ui/HeartRateDetectionScreen.kt`
```kotlin
if (detectionMode == HeartRateDetectionMode.DETAILED) {
    DetailedMetricsSection(
        hrvSdnnMs = hrvSdnnMs,
        hrvRmssdMs = hrvRmssdMs,
        afRiskProbability = afRiskProbability,
        irregularRiskLevel = irregularRiskLevel,
        irregularPulseHint = irregularPulseHint
    )
}
```

```kotlin
@Composable
private fun DetailedMetricsSection(
    hrvSdnnMs: Double?,
    hrvRmssdMs: Double?,
    afRiskProbability: Double?,
    irregularRiskLevel: String?,
    irregularPulseHint: String?
) {
    val riskLabel = irregularRiskLevel ?: "--"
    val riskKey = irregularRiskLevel?.lowercase()
    val riskColor = when {
        irregularRiskLevel == "?" || riskKey == "high" -> MaterialTheme.healthColors.critical
        irregularRiskLevel == "?" || riskKey == "medium" -> MaterialTheme.healthColors.warning
        irregularRiskLevel == "?" || riskKey == "low" -> MaterialTheme.healthColors.success
        else -> MaterialTheme.colorScheme.onSurfaceVariant
    }

    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text(text = "Detailed Metrics", fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            MetricCard(title = "HRV SDNN", value = formatMetric(hrvSdnnMs, 0), unit = "ms")
            MetricCard(title = "HRV RMSSD", value = formatMetric(hrvRmssdMs, 0), unit = "ms")
        }
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            MetricCard(title = "AF Risk Probability", value = formatPercent(afRiskProbability), unit = "%")
            MetricCard(title = "Irregular Risk", value = riskLabel, unit = "", color = riskColor)
        }
        if (!irregularPulseHint.isNullOrBlank()) {
            GlassCard(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.fillMaxWidth().padding(12.dp)) {
                    Text(text = "Nonspecific Irregularity Hint")
                    Text(text = irregularPulseHint)
                }
            }
        }
        DisclaimerSection()
    }
}
```

**Result Model (HRV/AF/Irregular Fields)**
File: `app/src/main/java/com/health/monitor/features/heartrate/domain/model/HeartRateResult.kt`
```kotlin
val hrvSdnnMs: Double? = null,
val hrvRmssdMs: Double? = null,
val afRiskProbability: Double? = null,
val irregularRiskLevel: String? = null,
val irregularPulseHint: String? = null,
```

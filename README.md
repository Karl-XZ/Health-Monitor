# Health Monitor (Android)

Offline-first health monitoring app that uses the phone camera for contact-based heart rate detection and facial vital-sign analysis. Single-module `app`, organized by feature packages.

**Product Positioning**
For everyday self-monitoring and trend tracking. Provides quick heart rate detection, facial analysis, and local history management.

**Key Features**
- Heart rate detection: PPG sampling, filtering, peak detection; outputs BPM, stability, confidence, and waveform
- Detailed mode: 60-second detection with HRV (SDNN/RMSSD), AF risk probability, irregular risk level, and hints
- Facial analysis: ML Kit face detection with brightness, symmetry, and color-related metrics
- Data management: local records, filters, stats, JSON export
- Multi-account and biometric login: PBKDF2 password hashing and optional biometrics
- Visualization and rules: trend charts and rule-based insights

**Important Notice**
This app provides health information and screening hints only. It is not a medical diagnosis. If you feel unwell, seek medical care. AF/irregular hints require ECG confirmation.

**Measurement Modes**
- Standard: 20 seconds, outputs BPM, stability, confidence
- Detailed: 60 seconds, adds HRV SDNN/RMSSD, AF risk probability, irregular risk level, and hints

**User Flow**
1. Register or sign in
2. Choose a heart rate mode and grant camera permission
3. Gently cover the rear camera and flashlight with a finger, keep steady
4. Review and save the result
5. View history, statistics, and exports in Data Management

**Data and Privacy**
- Offline storage by default, Room + SQLCipher local encryption
- Android Keystore for key management
- Images and key data encrypted at rest
- JSON export supported
- Internet permission is not enabled by default to keep the app offline

**Optional Cloud Analysis (Apimart)**
- Code: `app/src/main/java/com/health/monitor/features/facial/data/ApimartAiService.kt`
- Configure `APIMART_API_KEY` in `local.properties`, Gradle properties, or environment variables
- `AndroidManifest.xml` does not declare `android.permission.INTERNET` by default; add it manually if needed

**Project Structure**
- `app/src/main/java/com/health/monitor/`: app entry and navigation
- `app/src/main/java/com/health/monitor/features/`: feature code (auth / heartrate / facial / data / visualization / rules / camera)
- `app/src/main/java/com/health/monitor/core/`: data, security, DI, error handling
- `app/src/main/java/com/health/monitor/ui/`: theme and shared UI

**Requirements**
- Android Studio Hedgehog or newer
- Minimum SDK: `minSdk 26`

**Device Requirements**
- Rear camera and flashlight
- Front camera (for facial analysis)
- Biometrics (optional)

**Quick Start**
1. Open the project root in Android Studio
2. Ensure local JDK and SDK versions meet requirements
3. Run Gradle sync

**CLI Build**
```bash
./gradlew assembleDebug
```

**Permissions**
- `android.permission.CAMERA`
- `android.permission.READ_EXTERNAL_STORAGE` (<= 32, for export)
- `android.permission.WRITE_EXTERNAL_STORAGE` (<= 28, for export)

**Data Export**
- Export folder: `exports` under the app external files directory
- Code: `app/src/main/java/com/health/monitor/core/data/HealthDataExporter.kt`

**FAQ**
- Detailed mode data is empty: ensure you run the full 60-second detection
- Waveform is unstable: keep the finger steady and ensure adequate light
- Online analysis unavailable: `android.permission.INTERNET` is disabled by default

**Implementation Docs**
- `HEART_RATE_DETECTION_IMPL.md`

## Third-party libraries & references

This project does not use any external training dataset. All measurements are derived from on-device camera frames and local signal/statistical processing.

Third-party libraries and tools used in this project (declared in `app/build.gradle.kts`) include Kotlin/AndroidX Jetpack components (Compose, Navigation, Lifecycle, Activity), CameraX for camera frame capture, ML Kit Face Detection for on-device face detection, Hilt for dependency injection, Room for local persistence, SQLCipher for encrypted local database storage, OkHttp for optional networking, Kotlin Coroutines for async processing, MPAndroidChart for charts, Coil for image loading, Gson for JSON serialization, AndroidX Biometric for optional biometric unlock, and AndroidX DataStore for preferences.

Key external documentation / references for concepts and APIs:
- CameraX documentation: https://developer.android.com/media/camera/camerax
- ML Kit Face Detection documentation: https://developers.google.com/ml-kit/vision/face-detection/android
- ML Kit terms (for the face-detection SDK): https://developers.google.com/ml-kit/terms
- PPG (photoplethysmography) background: https://en.wikipedia.org/wiki/Photoplethysmogram
- HRV standards (SDNN/RMSSD and interpretation): https://www.ahajournals.org/doi/10.1161/01.cir.93.5.1043


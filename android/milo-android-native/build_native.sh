#!/usr/bin/env bash
set -e

PROJECT_DIR="/home/jeffy/milo-android-native"
BUILD_DIR="${PROJECT_DIR}/build"
SDK_DIR="/home/jeffy/.build-tools/android-sdk"
JDK_DIR="/home/jeffy/.build-tools/jdk"

export JAVA_HOME="${JDK_DIR}"
export PATH="${JAVA_HOME}/bin:${SDK_DIR}/build-tools/34.0.0:${PATH}"

AAPT2="${SDK_DIR}/build-tools/34.0.0/aapt2"
D8="${SDK_DIR}/build-tools/34.0.0/d8"
ZIPALIGN="${SDK_DIR}/build-tools/34.0.0/zipalign"
APKSIGNER="${SDK_DIR}/build-tools/34.0.0/apksigner"
ANDROID_JAR="${SDK_DIR}/platforms/android-34/android.jar"

echo "🔨 [1/6] Cleaning and preparing build directories..."
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}/compiled_res" "${BUILD_DIR}/gen" "${BUILD_DIR}/obj" "${BUILD_DIR}/apk"

echo "🎨 [2/6] Compiling Android resources with AAPT2..."
"${AAPT2}" compile --dir "${PROJECT_DIR}/res" -o "${BUILD_DIR}/compiled_res/resources.zip"

echo "🔗 [3/6] Linking resources and generating R.java..."
"${AAPT2}" link \
    -I "${ANDROID_JAR}" \
    --manifest "${PROJECT_DIR}/AndroidManifest.xml" \
    --java "${BUILD_DIR}/gen" \
    -o "${BUILD_DIR}/app-unaligned.apk" \
    --auto-add-overlay \
    "${BUILD_DIR}/compiled_res/resources.zip"

echo "☕ [4/6] Compiling Pure Native Java code with javac..."
javac \
    -encoding UTF-8 \
    -cp "${ANDROID_JAR}" \
    -d "${BUILD_DIR}/obj" \
    "${BUILD_DIR}/gen/ai/milo/nativecall/R.java" \
    "${PROJECT_DIR}/src/ai/milo/nativecall"/*.java

echo "📦 [5/6] Dexing bytecode with D8..."
"${D8}" \
    --lib "${ANDROID_JAR}" \
    --output "${BUILD_DIR}/apk" \
    "${BUILD_DIR}/obj/ai/milo/nativecall"/*.class

# Add classes.dex into app-unaligned.apk
cd "${BUILD_DIR}/apk"
"${JDK_DIR}/bin/jar" -uf "${BUILD_DIR}/app-unaligned.apk" classes.dex
cd "${PROJECT_DIR}"

echo "🔏 [6/6] Aligning and signing Pure Native APK..."
"${ZIPALIGN}" -f -p 4 "${BUILD_DIR}/app-unaligned.apk" "${BUILD_DIR}/app-aligned.apk"

# Generate keystore if not exists
KEYSTORE="${PROJECT_DIR}/milo-native-release.keystore"
if [ ! -f "${KEYSTORE}" ]; then
    keytool -genkeypair \
        -keystore "${KEYSTORE}" \
        -storepass milo12345 \
        -alias milo \
        -keypass milo12345 \
        -keyalg RSA \
        -keysize 2048 \
        -validity 10000 \
        -dname "CN=Milo AI Native, OU=Directing, O=Milo Ecosystem, L=Chennai, ST=TN, C=IN"
fi

OUTPUT_APK="${PROJECT_DIR}/MiloNativeCall.apk"
"${APKSIGNER}" sign \
    --ks "${KEYSTORE}" \
    --ks-pass pass:milo12345 \
    --ks-key-alias milo \
    --key-pass pass:milo12345 \
    --out "${OUTPUT_APK}" \
    "${BUILD_DIR}/app-aligned.apk"

echo "✨ Verifying Pure Native APK signature..."
"${APKSIGNER}" verify "${OUTPUT_APK}"

echo "✅ MiloNativeCall.apk successfully built at: ${OUTPUT_APK}"
ls -lh "${OUTPUT_APK}"

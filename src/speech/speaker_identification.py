"""
Speaker Identification and Voice Separation
Identifies who is speaking for accurate nomination tracking
"""

import asyncio
import logging
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Optional dependencies - handle gracefully if missing
try:
    import numpy as np

    NDArray = np.ndarray
except ImportError:
    np = None
    NDArray = Any

try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
except ImportError:
    KMeans = None
    StandardScaler = None

try:
    import librosa
except ImportError:
    librosa = None


@dataclass
class SpeakerProfile:
    """Profile for a known speaker"""

    name: str
    voice_features: NDArray
    confidence_threshold: float = 0.7
    sample_count: int = 0


class VoiceFeatureExtractor:
    """Extracts voice features for speaker identification"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Feature extraction parameters
        self.sample_rate = 16000
        self.n_mfcc = 13
        self.n_chroma = 12
        self.n_mel = 8
        self.hop_length = 512

    def extract_features(self, audio_data: NDArray, sample_rate: int = None) -> NDArray:
        """Extract voice features from audio"""
        try:
            if sample_rate is None:
                sample_rate = self.sample_rate

            # Ensure audio is float32
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32) / 32768.0

            # Extract features
            features = []

            # MFCC features (main voice characteristics)
            mfccs = librosa.feature.mfcc(
                y=audio_data,
                sr=sample_rate,
                n_mfcc=self.n_mfcc,
                hop_length=self.hop_length,
            )
            features.extend(np.mean(mfccs, axis=1))
            features.extend(np.std(mfccs, axis=1))

            # Chroma features (pitch)
            chroma = librosa.feature.chroma_stft(
                y=audio_data, sr=sample_rate, hop_length=self.hop_length
            )
            features.extend(np.mean(chroma, axis=1))
            features.extend(np.std(chroma, axis=1))

            # Mel-frequency features
            mel = librosa.feature.melspectrogram(
                y=audio_data, sr=sample_rate, hop_length=self.hop_length
            )
            features.extend(np.mean(mel, axis=1))
            features.extend(np.std(mel, axis=1))

            # Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(
                y=audio_data, sr=sample_rate, hop_length=self.hop_length
            )[0]
            features.append(np.mean(spectral_centroids))
            features.append(np.std(spectral_centroids))

            # Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(
                audio_data, hop_length=self.hop_length
            )[0]
            features.append(np.mean(zcr))
            features.append(np.std(zcr))

            return np.array(features)

        except Exception as e:
            self.logger.error(f"Feature extraction failed: {e}")
            return np.array([])


class SpeakerIdentifier:
    """Identifies speakers from voice features"""

    def __init__(self, profiles_file: str = "speaker_profiles.pkl"):
        self.logger = logging.getLogger(__name__)
        self.profiles_file = Path(profiles_file)

        # Components
        self.feature_extractor = VoiceFeatureExtractor()
        self.scaler = StandardScaler()

        # Speaker data
        self.speaker_profiles: Dict[str, SpeakerProfile] = {}
        self.is_trained = False

        # Load existing profiles
        self.load_profiles()

    def add_speaker_sample(
        self, name: str, audio_data: NDArray, sample_rate: int = 16000
    ):
        """Add a voice sample for a speaker"""
        try:
            # Extract features
            features = self.feature_extractor.extract_features(audio_data, sample_rate)

            if len(features) == 0:
                self.logger.warning(f"Could not extract features for {name}")
                return False

            # Add to speaker profile
            if name in self.speaker_profiles:
                # Update existing profile (running average)
                profile = self.speaker_profiles[name]
                profile.sample_count += 1
                alpha = 1.0 / profile.sample_count  # Learning rate
                profile.voice_features = (
                    1 - alpha
                ) * profile.voice_features + alpha * features
            else:
                # Create new profile
                self.speaker_profiles[name] = SpeakerProfile(
                    name=name, voice_features=features, sample_count=1
                )

            self.logger.info(
                f"Added voice sample for {name} (total samples: {
                    self.speaker_profiles[name].sample_count})")

            # Retrain if we have multiple speakers
            if len(self.speaker_profiles) > 1:
                self._train_classifier()

            return True

        except Exception as e:
            self.logger.error(f"Error adding speaker sample for {name}: {e}")
            return False

    def identify_speaker(
        self, audio_data: NDArray, sample_rate: int = 16000
    ) -> Tuple[Optional[str], float]:
        """Identify speaker from audio"""
        try:
            if not self.speaker_profiles:
                return None, 0.0

            # Extract features
            features = self.feature_extractor.extract_features(audio_data, sample_rate)

            if len(features) == 0:
                return None, 0.0

            # Compare with known speakers
            best_match = None
            best_similarity = 0.0

            for profile in self.speaker_profiles.values():
                # Calculate similarity (cosine similarity)
                similarity = self._calculate_similarity(
                    features, profile.voice_features
                )

                if (
                    similarity > best_similarity
                    and similarity > profile.confidence_threshold
                ):
                    best_similarity = similarity
                    best_match = profile.name

            return best_match, best_similarity

        except Exception as e:
            self.logger.error(f"Speaker identification failed: {e}")
            return None, 0.0

    def _calculate_similarity(self, features1: NDArray, features2: NDArray) -> float:
        """Calculate similarity between feature vectors"""
        try:
            # Normalize features
            norm1 = np.linalg.norm(features1)
            norm2 = np.linalg.norm(features2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            # Cosine similarity
            similarity = np.dot(features1, features2) / (norm1 * norm2)

            # Convert to 0-1 range
            return (similarity + 1) / 2

        except Exception:
            return 0.0

    def _train_classifier(self):
        """Train classifier on speaker profiles"""
        try:
            if len(self.speaker_profiles) < 2:
                return

            # Prepare training data
            features_list = []
            for profile in self.speaker_profiles.values():
                features_list.append(profile.voice_features)

            # Fit scaler
            self.scaler.fit(features_list)
            self.is_trained = True

            self.logger.info(
                f"Trained classifier on {len(self.speaker_profiles)} speakers"
            )

        except Exception as e:
            self.logger.error(f"Classifier training failed: {e}")

    def save_profiles(self):
        """Save speaker profiles to file"""
        try:
            data = {
                "profiles": self.speaker_profiles,
                "scaler": self.scaler,
                "is_trained": self.is_trained,
            }

            with open(self.profiles_file, "wb") as f:
                pickle.dump(data, f)

            self.logger.info(f"Saved {len(self.speaker_profiles)} speaker profiles")

        except Exception as e:
            self.logger.error(f"Failed to save profiles: {e}")

    def load_profiles(self):
        """Load speaker profiles from file"""
        try:
            if not self.profiles_file.exists():
                return

            with open(self.profiles_file, "rb") as f:
                data = pickle.load(f)

            self.speaker_profiles = data.get("profiles", {})
            self.scaler = data.get("scaler", StandardScaler())
            self.is_trained = data.get("is_trained", False)

            self.logger.info(f"Loaded {len(self.speaker_profiles)} speaker profiles")

        except Exception as e:
            self.logger.error(f"Failed to load profiles: {e}")

    def remove_speaker(self, name: str) -> bool:
        """Remove a speaker profile"""
        if name in self.speaker_profiles:
            del self.speaker_profiles[name]
            self.logger.info(f"Removed speaker profile for {name}")

            # Retrain if needed
            if len(self.speaker_profiles) > 1:
                self._train_classifier()
            else:
                self.is_trained = False

            return True

        return False

    def get_speakers(self) -> List[str]:
        """Get list of known speakers"""
        return list(self.speaker_profiles.keys())

    def get_speaker_info(self, name: str) -> Optional[Dict]:
        """Get information about a speaker"""
        if name in self.speaker_profiles:
            profile = self.speaker_profiles[name]
            return {
                "name": profile.name,
                "sample_count": profile.sample_count,
                "confidence_threshold": profile.confidence_threshold,
                "feature_count": len(profile.voice_features),
            }
        return None


class VoiceSeparationSystem:
    """Complete voice separation and identification system"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.speaker_id = SpeakerIdentifier()

        # Training mode
        self.training_mode = False
        self.current_training_speaker = None

    def enter_training_mode(self, speaker_name: str):
        """Enter training mode for a specific speaker"""
        self.training_mode = True
        self.current_training_speaker = speaker_name
        self.logger.info(f"Entered training mode for {speaker_name}")

    def exit_training_mode(self):
        """Exit training mode"""
        self.training_mode = False
        self.current_training_speaker = None
        self.speaker_id.save_profiles()
        self.logger.info("Exited training mode")

    def process_audio(self, audio_data: NDArray, sample_rate: int = 16000) -> Dict:
        """Process audio for speaker identification or training"""
        result = {"speaker": None, "confidence": 0.0, "training": self.training_mode}

        try:
            if self.training_mode and self.current_training_speaker:
                # Training mode - add sample
                success = self.speaker_id.add_speaker_sample(
                    self.current_training_speaker, audio_data, sample_rate
                )
                result["training_success"] = success
                result["speaker"] = self.current_training_speaker

            else:
                # Identification mode
                speaker, confidence = self.speaker_id.identify_speaker(
                    audio_data, sample_rate
                )
                result["speaker"] = speaker
                result["confidence"] = confidence

            return result

        except Exception as e:
            self.logger.error(f"Audio processing failed: {e}")
            result["error"] = str(e)
            return result

    def get_known_speakers(self) -> List[str]:
        """Get list of known speakers"""
        return self.speaker_id.get_speakers()

    def remove_speaker(self, name: str) -> bool:
        """Remove a speaker"""
        return self.speaker_id.remove_speaker(name)


# Example usage and testing
async def test_speaker_identification():
    """Test speaker identification system"""

    system = VoiceSeparationSystem()

    print("🎤 Speaker Identification Test")
    print("Available speakers:", system.get_known_speakers())

    # Example: Train with sample audio (would be real audio in practice)
    print("\n📚 Training mode example:")
    system.enter_training_mode("Alice")

    # Simulate training samples (would be real audio)
    for i in range(3):
        fake_audio = np.random.randn(16000).astype(np.float32)  # 1 second of fake audio
        result = system.process_audio(fake_audio)
        print(f"Training sample {i + 1}: {result}")

    system.exit_training_mode()

    # Example: Identify speaker
    print("\n🔍 Identification mode:")
    fake_audio = np.random.randn(16000).astype(np.float32)
    result = system.process_audio(fake_audio)
    print(f"Identification result: {result}")


if __name__ == "__main__":
    asyncio.run(test_speaker_identification())

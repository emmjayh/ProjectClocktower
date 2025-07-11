"""
Voice Player Identification System
Identifies players by their voice characteristics for secure game actions
"""

import asyncio
import logging
# Simplified voice identification without numpy dependency
try:
    import numpy as np
except ImportError:
    # Mock numpy for environments without it
    class MockNumpy:
        def array(self, data):
            return data
        def mean(self, data):
            return sum(data) / len(data) if data else 0
        def std(self, data):
            if not data:
                return 0
            mean_val = self.mean(data)
            variance = sum((x - mean_val) ** 2 for x in data) / len(data)
            return variance ** 0.5
        def zeros(self, size):
            return [0] * size
        def dot(self, a, b):
            return sum(x * y for x, y in zip(a, b))
        def linalg(self):
            return MockLinalg()
        def sum(self, data):
            return sum(data) if data else 0
        def frombuffer(self, data, dtype=None):
            return list(data)
        def fft(self):
            return MockFFT()
        def argmax(self, data):
            return data.index(max(data)) if data else 0
    
    class MockLinalg:
        def norm(self, data):
            return sum(x * x for x in data) ** 0.5 if data else 0
    
    class MockFFT:
        def fft(self, data):
            return data  # Simplified
        def fftfreq(self, n, d):
            return list(range(n))
    
    np = MockNumpy()
    np.linalg = MockLinalg()
    np.fft = MockFFT()
    np.ndarray = list  # For type annotations
import tempfile
import wave
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path

from .speech_handler import SpeechHandler


@dataclass
class VoiceProfile:
    """Voice profile for a player"""
    player_name: str
    voice_embeddings: List[np.ndarray]
    last_updated: float
    confidence_threshold: float = 0.75
    training_samples: int = 0


class VoiceFeatureExtractor:
    """Extracts voice features for identification"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Simple voice features (in production, use more sophisticated methods)
        self.features = [
            "pitch_mean",
            "pitch_std", 
            "energy_mean",
            "energy_std",
            "spectral_centroid",
            "zero_crossing_rate",
            "mfcc_mean",
            "mfcc_std"
        ]
        
    def extract_features(self, audio_data: bytes, sample_rate: int = 16000) -> np.ndarray:
        """Extract voice features from audio data"""
        
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            audio_array = audio_array.astype(np.float32) / 32768.0  # Normalize
            
            features = []
            
            # Basic pitch estimation (simplified)
            pitch_values = self._estimate_pitch(audio_array, sample_rate)
            features.extend([
                np.mean(pitch_values),
                np.std(pitch_values)
            ])
            
            # Energy features
            energy = audio_array ** 2
            features.extend([
                np.mean(energy),
                np.std(energy)
            ])
            
            # Spectral features (simplified)
            fft = np.fft.fft(audio_array)
            magnitude = np.abs(fft[:len(fft)//2])
            frequencies = np.fft.fftfreq(len(fft), 1/sample_rate)[:len(fft)//2]
            
            # Spectral centroid
            spectral_centroid = np.sum(frequencies * magnitude) / np.sum(magnitude)
            features.append(spectral_centroid)
            
            # Zero crossing rate
            zero_crossings = np.sum(np.diff(np.sign(audio_array)) != 0)
            zcr = zero_crossings / len(audio_array)
            features.append(zcr)
            
            # Simplified MFCC-like features
            mel_features = self._extract_mel_features(magnitude, sample_rate)
            features.extend([
                np.mean(mel_features),
                np.std(mel_features)
            ])
            
            return np.array(features)
            
        except Exception as e:
            self.logger.error(f"Failed to extract voice features: {e}")
            return np.zeros(len(self.features))
            
    def _estimate_pitch(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Simple pitch estimation using autocorrelation"""
        
        # Window size for pitch estimation
        window_size = int(sample_rate * 0.03)  # 30ms windows
        hop_size = window_size // 2
        
        pitch_values = []
        
        for i in range(0, len(audio) - window_size, hop_size):
            window = audio[i:i + window_size]
            
            # Autocorrelation
            autocorr = np.correlate(window, window, mode='full')
            autocorr = autocorr[len(autocorr)//2:]
            
            # Find peak (simplified)
            min_period = int(sample_rate / 400)  # 400 Hz max
            max_period = int(sample_rate / 80)   # 80 Hz min
            
            if len(autocorr) > max_period:
                peak_idx = np.argmax(autocorr[min_period:max_period]) + min_period
                pitch = sample_rate / peak_idx if peak_idx > 0 else 0
                pitch_values.append(pitch)
                
        return np.array(pitch_values) if pitch_values else np.array([0])
        
    def _extract_mel_features(self, magnitude: np.ndarray, sample_rate: int) -> np.ndarray:
        """Extract simplified mel-scale features"""
        
        # Simple mel-scale approximation
        mel_filters = 13
        mel_features = []
        
        for i in range(mel_filters):
            start_freq = i * (sample_rate // 2) // mel_filters
            end_freq = (i + 1) * (sample_rate // 2) // mel_filters
            
            start_bin = int(start_freq * len(magnitude) * 2 / sample_rate)
            end_bin = int(end_freq * len(magnitude) * 2 / sample_rate)
            
            if end_bin > start_bin and end_bin < len(magnitude):
                mel_energy = np.sum(magnitude[start_bin:end_bin])
                mel_features.append(mel_energy)
                
        return np.array(mel_features) if mel_features else np.array([0])


class VoicePlayerIdentifier:
    """Main voice identification system"""
    
    def __init__(self, speech_handler: SpeechHandler, player_names: List[str]):
        self.speech_handler = speech_handler
        self.player_names = player_names
        self.logger = logging.getLogger(__name__)
        
        # Voice profiles for each player
        self.voice_profiles: Dict[str, VoiceProfile] = {}
        
        # Feature extractor
        self.feature_extractor = VoiceFeatureExtractor()
        
        # Identification settings
        self.min_training_samples = 3
        self.identification_threshold = 0.7
        self.max_profile_age = 3600  # 1 hour
        
    async def initialize_voice_profiles(self) -> bool:
        """Initialize voice profiles for all players"""
        
        try:
            await self.speech_handler.speak(
                "Voice identification setup required. Each player will record their voice."
            )
            
            for player_name in self.player_names:
                success = await self._train_player_voice(player_name)
                if not success:
                    self.logger.warning(f"Failed to train voice for {player_name}")
                    
            trained_count = len(self.voice_profiles)
            await self.speech_handler.speak(
                f"Voice profiles created for {trained_count} out of {len(self.player_names)} players."
            )
            
            return trained_count >= len(self.player_names) // 2  # At least half
            
        except Exception as e:
            self.logger.error(f"Failed to initialize voice profiles: {e}")
            return False
            
    async def _train_player_voice(self, player_name: str) -> bool:
        """Train voice profile for a specific player"""
        
        try:
            await self.speech_handler.speak(
                f"{player_name}, please say your name clearly three times for voice training."
            )
            
            voice_samples = []
            
            for attempt in range(3):
                await self.speech_handler.speak(f"Recording {attempt + 1}. Say your name now.")
                
                # Record audio sample
                audio_data = await self._record_voice_sample(timeout=5.0)
                
                if audio_data:
                    # Extract features
                    features = self.feature_extractor.extract_features(audio_data)
                    voice_samples.append(features)
                    await self.speech_handler.speak("Sample recorded.")
                else:
                    await self.speech_handler.speak("No voice detected. Try again.")
                    
            if len(voice_samples) >= self.min_training_samples:
                # Create voice profile
                import time
                profile = VoiceProfile(
                    player_name=player_name,
                    voice_embeddings=voice_samples,
                    last_updated=time.time(),
                    training_samples=len(voice_samples)
                )
                
                self.voice_profiles[player_name] = profile
                
                await self.speech_handler.speak(f"Voice profile created for {player_name}.")
                return True
            else:
                await self.speech_handler.speak(f"Failed to get enough voice samples for {player_name}.")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to train voice for {player_name}: {e}")
            return False
            
    async def _record_voice_sample(self, timeout: float = 5.0) -> Optional[bytes]:
        """Record a voice sample for training or identification"""
        
        try:
            # Use speech handler's audio recording capability
            audio_data = await self.speech_handler._record_audio(timeout)
            return audio_data
            
        except Exception as e:
            self.logger.error(f"Failed to record voice sample: {e}")
            return None
            
    async def identify_speaker(self, audio_data: bytes = None, timeout: float = 3.0) -> Tuple[Optional[str], float]:
        """Identify speaker from audio sample"""
        
        if not self.voice_profiles:
            return None, 0.0
            
        # Record audio if not provided
        if audio_data is None:
            audio_data = await self._record_voice_sample(timeout)
            
        if not audio_data:
            return None, 0.0
            
        try:
            # Extract features from audio
            features = self.feature_extractor.extract_features(audio_data)
            
            best_match = None
            best_score = 0.0
            
            # Compare against all voice profiles
            for player_name, profile in self.voice_profiles.items():
                score = self._calculate_voice_similarity(features, profile)
                
                if score > best_score and score > self.identification_threshold:
                    best_score = score
                    best_match = player_name
                    
            return best_match, best_score
            
        except Exception as e:
            self.logger.error(f"Failed to identify speaker: {e}")
            return None, 0.0
            
    def _calculate_voice_similarity(self, features: np.ndarray, profile: VoiceProfile) -> float:
        """Calculate similarity between features and voice profile"""
        
        if len(profile.voice_embeddings) == 0:
            return 0.0
            
        # Calculate distance to each embedding in the profile
        similarities = []
        
        for embedding in profile.voice_embeddings:
            # Cosine similarity
            dot_product = np.dot(features, embedding)
            norm_product = np.linalg.norm(features) * np.linalg.norm(embedding)
            
            if norm_product > 0:
                similarity = dot_product / norm_product
                similarities.append(similarity)
                
        if not similarities:
            return 0.0
            
        # Return average similarity
        return np.mean(similarities)
        
    async def verify_player_identity(self, claimed_name: str, max_attempts: int = 3) -> bool:
        """Verify a player's identity through voice"""
        
        if claimed_name not in self.voice_profiles:
            return False
            
        await self.speech_handler.speak(
            f"{claimed_name}, please say your name to verify your identity."
        )
        
        for attempt in range(max_attempts):
            identified_name, confidence = await self.identify_speaker()
            
            if identified_name == claimed_name and confidence > self.identification_threshold:
                await self.speech_handler.speak("Identity verified.")
                return True
            elif identified_name != claimed_name and identified_name is not None:
                await self.speech_handler.speak(
                    f"Voice matches {identified_name}, not {claimed_name}. Try again."
                )
            else:
                await self.speech_handler.speak("Could not identify voice. Try again.")
                
        await self.speech_handler.speak("Identity verification failed.")
        return False
        
    async def secure_command_with_voice_id(self, command_text: str) -> Tuple[Optional[str], str]:
        """Process a command with voice identification for security"""
        
        await self.speech_handler.speak("Please say your name to identify yourself.")
        
        identified_player, confidence = await self.identify_speaker()
        
        if identified_player and confidence > self.identification_threshold:
            return identified_player, command_text
        else:
            await self.speech_handler.speak("Could not identify speaker. Command ignored.")
            return None, command_text
            
    def update_voice_profile(self, player_name: str, new_features: np.ndarray):
        """Update voice profile with new sample"""
        
        if player_name in self.voice_profiles:
            profile = self.voice_profiles[player_name]
            
            # Add new sample (with max limit)
            profile.voice_embeddings.append(new_features)
            if len(profile.voice_embeddings) > 10:  # Keep last 10 samples
                profile.voice_embeddings.pop(0)
                
            import time
            profile.last_updated = time.time()
            profile.training_samples += 1
            
    def get_identification_stats(self) -> Dict[str, Any]:
        """Get voice identification system statistics"""
        
        stats = {
            "total_profiles": len(self.voice_profiles),
            "min_samples": min(p.training_samples for p in self.voice_profiles.values()) if self.voice_profiles else 0,
            "max_samples": max(p.training_samples for p in self.voice_profiles.values()) if self.voice_profiles else 0,
            "avg_samples": np.mean([p.training_samples for p in self.voice_profiles.values()]) if self.voice_profiles else 0,
            "identification_threshold": self.identification_threshold
        }
        
        return stats


class SecureVoiceActions:
    """Secure game actions requiring voice identification"""
    
    def __init__(self, voice_identifier: VoicePlayerIdentifier):
        self.voice_identifier = voice_identifier
        self.logger = logging.getLogger(__name__)
        
        # Actions that require voice identification
        self.secure_actions = {
            "nominate",
            "vote", 
            "claim",
            "ability_target"
        }
        
    async def process_secure_command(self, action_type: str, command_data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """Process a command that requires voice identification"""
        
        if action_type not in self.secure_actions:
            return True, "No identification required", command_data
            
        # Get voice identification
        identified_player, confidence = await self.voice_identifier.identify_speaker()
        
        if not identified_player:
            return False, "Could not identify speaker", command_data
            
        if confidence < self.voice_identifier.identification_threshold:
            return False, f"Voice identification confidence too low: {confidence:.2f}", command_data
            
        # Add identified player to command data
        command_data["identified_player"] = identified_player
        command_data["voice_confidence"] = confidence
        
        return True, f"Identified as {identified_player}", command_data
        
    async def secure_nomination(self, nominee: str) -> Tuple[bool, str, str]:
        """Secure nomination with voice identification"""
        
        identified_player, confidence = await self.voice_identifier.identify_speaker()
        
        if not identified_player:
            return False, "Could not identify nominator", ""
            
        success = await self.voice_identifier.verify_player_identity(identified_player)
        
        if success:
            return True, f"Nomination by {identified_player}", identified_player
        else:
            return False, "Voice verification failed", ""
            
    async def secure_vote(self, vote_value: bool) -> Tuple[bool, str, str]:
        """Secure vote with voice identification"""
        
        identified_player, confidence = await self.voice_identifier.identify_speaker()
        
        if not identified_player:
            return False, "Could not identify voter", ""
            
        if confidence > self.voice_identifier.identification_threshold:
            return True, f"Vote by {identified_player}", identified_player
        else:
            return False, f"Voice confidence too low: {confidence:.2f}", ""


if __name__ == "__main__":
    # Test voice identification
    async def test_voice_identification():
        from .speech_handler import SpeechHandler, SpeechConfig
        
        speech_handler = SpeechHandler(SpeechConfig())
        await speech_handler.initialize()
        
        player_names = ["Alice", "Bob", "Charlie"]
        voice_id = VoicePlayerIdentifier(speech_handler, player_names)
        
        # Initialize profiles
        success = await voice_id.initialize_voice_profiles()
        print(f"Voice profile initialization: {success}")
        
        if success:
            # Test identification
            print("Testing voice identification...")
            identified, confidence = await voice_id.identify_speaker()
            print(f"Identified: {identified} (confidence: {confidence:.2f})")
            
        speech_handler.cleanup()
        
    asyncio.run(test_voice_identification())
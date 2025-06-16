from locust import HttpUser, task, between
import os

class MedicalApiUser(HttpUser):
    wait_time = between(2, 5)  # Simulate user think time (2-5 seconds)

    @task(1)
    def upload_audio(self):
        """Test POST /upload endpoint with audio file."""
        with open("WhatsApp Ptt 2025-06-03 at 1.46.58 PM.ogg", "rb") as audio_file:
            files = {"audio": ("WhatsApp Ptt 2025-06-03 at 1.46.58 PM.ogg", audio_file, "audio/wav")}
            data = {
                "clinicalSheet": "Medical Reports",
                "language": "ar",
                "isConversation": "off",
                "doctorName": "Dr. Test"
            }
            self.client.post("/upload", files=files, data=data)

# Run with: locust -f load_test.py --host=http://localhost:8587
// Face Scanning JavaScript
// Real-time face recognition using WebSocket

let socket = null;
let video = null;
let stream = null;
let isScanning = false;
let currentRecognition = null;

document.addEventListener('DOMContentLoaded', function() {
    video = document.getElementById('videoElement');
    const startBtn = document.getElementById('startScanning');
    const stopBtn = document.getElementById('stopScanning');
    const resultDiv = document.getElementById('recognitionResult');
    const approveBtn = document.getElementById('approveBtn');
    const denyBtn = document.getElementById('denyBtn');
    const continueBtn = document.getElementById('continueBtn');
    
    startBtn.addEventListener('click', startScanning);
    stopBtn.addEventListener('click', stopScanning);
    approveBtn.addEventListener('click', handleApprove);
    denyBtn.addEventListener('click', handleDeny);
    continueBtn.addEventListener('click', continueScanning);
    
    // Initialize SocketIO connection
    socket = io();
    
    socket.on('connect', function() {
        console.log('Connected to server');
    });
    
    socket.on('recognition_result', function(data) {
        handleRecognitionResult(data);
    });
    
    socket.on('error', function(data) {
        showError(data.message || 'An error occurred');
    });
});

function startScanning() {
    if (isScanning) return;
    
    // Request camera access
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(function(mediaStream) {
            stream = mediaStream;
            video.srcObject = stream;
            isScanning = true;
            
            document.getElementById('startScanning').style.display = 'none';
            document.getElementById('stopScanning').style.display = 'block';
            
            // Send frames to server via WebSocket
            sendFrames();
            
            // Request server to start recognition
            socket.emit('start_recognition', { bus_id: busId });
        })
        .catch(function(err) {
            console.error('Error accessing camera:', err);
            alert('Could not access camera. Please check permissions.');
        });
}

function stopScanning() {
    if (!isScanning) return;
    
    isScanning = false;
    
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
    
    video.srcObject = null;
    
    document.getElementById('startScanning').style.display = 'block';
    document.getElementById('stopScanning').style.display = 'none';
    
    socket.emit('stop_recognition');
    
    hideResult();
}

function sendFrames() {
    if (!isScanning || !video) return;
    
    // Check if video is ready
    if (video.readyState !== video.HAVE_ENOUGH_DATA) {
        setTimeout(sendFrames, 200); // Wait if video not ready
        return;
    }
    
    const canvas = document.createElement('canvas');
    // Limit resolution to reduce processing load
    const maxWidth = 640;
    const maxHeight = 480;
    
    let width = video.videoWidth;
    let height = video.videoHeight;
    
    // Scale down if too large
    if (width > maxWidth || height > maxHeight) {
        const scale = Math.min(maxWidth / width, maxHeight / height);
        width = Math.floor(width * scale);
        height = Math.floor(height * scale);
    }
    
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, width, height);
    
    // Convert to base64 with lower quality to reduce size
    const frameData = canvas.toDataURL('image/jpeg', 0.6); // Lower quality
    
    // Send to server
    socket.emit('video_frame', { frame: frameData });
    
    // Send next frame after delay (reduced to ~5 FPS to prevent overload)
    setTimeout(sendFrames, 200); // ~5 FPS (was 100ms = 10 FPS)
}

function handleRecognitionResult(data) {
    if (!data || !data.recognized) {
        return; // No recognition
    }
    
    currentRecognition = data;
    
    const resultDiv = document.getElementById('recognitionResult');
    const statusIcon = document.getElementById('statusIcon');
    const studentName = document.getElementById('studentName');
    const studentInfo = document.getElementById('studentInfo');
    const confidenceInfo = document.getElementById('confidenceInfo');
    const approveBtn = document.getElementById('approveBtn');
    const denyBtn = document.getElementById('denyBtn');
    const continueBtn = document.getElementById('continueBtn');
    
    studentName.textContent = data.student_name || 'Unknown';
    studentInfo.textContent = data.student_id ? `ID: ${data.student_id}` : '';
    confidenceInfo.textContent = `Confidence: ${data.confidence.toFixed(1)}%`;
    
    if (data.is_assigned) {
        // Student is assigned to this bus
        resultDiv.className = 'recognition-result show granted';
        statusIcon.textContent = '✓';
        statusIcon.style.color = 'var(--success-color)';
        studentInfo.textContent += ' | Assigned to this bus';
        approveBtn.style.display = 'inline-block';
        denyBtn.style.display = 'inline-block';
        continueBtn.style.display = 'none';
    } else {
        // Student not assigned
        resultDiv.className = 'recognition-result show denied';
        statusIcon.textContent = '✗';
        statusIcon.style.color = 'var(--error-color)';
        studentInfo.textContent += ' | NOT assigned to this bus';
        approveBtn.style.display = 'none';
        denyBtn.style.display = 'inline-block';
        continueBtn.style.display = 'inline-block';
    }
}

function handleApprove() {
    if (!currentRecognition) return;
    
    logRecognition(true, '');
    hideResult();
    continueScanning();
}

function handleDeny() {
    if (!currentRecognition) return;
    
    const reason = prompt('Reason for denial (optional):') || 'Not assigned to bus';
    logRecognition(false, reason);
    hideResult();
    continueScanning();
}

function continueScanning() {
    hideResult();
    currentRecognition = null;
}

function hideResult() {
    const resultDiv = document.getElementById('recognitionResult');
    resultDiv.classList.remove('show');
}

function logRecognition(accessGranted, reason) {
    if (!currentRecognition) return;
    
    fetch('/driver/api/log-recognition', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            student_id: currentRecognition.student_id,
            bus_id: busId,
            confidence: currentRecognition.confidence,
            access_granted: accessGranted,
            reason: reason
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Recognition logged');
        }
    })
    .catch(error => {
        console.error('Error logging recognition:', error);
    });
}

function showError(message) {
    alert('Error: ' + message);
}


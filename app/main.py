from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from app.api.routes import router

app = FastAPI(
    title="Email Validator API",
    description="A comprehensive email validation service that checks email format, DNS records, and SMTP connectivity",
    version="1.0.0"
)

app.include_router(router, prefix="/api")

@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Simple web interface for the email validator
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Email Validator</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .container { background: #f5f5f5; padding: 20px; border-radius: 8px; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input[type="file"], input[type="checkbox"] { margin-bottom: 10px; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .status { margin-top: 20px; padding: 10px; border-radius: 4px; }
            .success { background: #d4edda; color: #155724; }
            .error { background: #f8d7da; color: #721c24; }
            .info { background: #d1ecf1; color: #0c5460; }
            .api-info { background: #e2e3e5; padding: 15px; border-radius: 4px; margin-top: 20px; }
        </style>
    </head>
    <body>
        <h1>Email Validator</h1>
        <div class="container">
            <form id="uploadForm">
                <div class="form-group">
                    <label for="file">Select CSV file with email addresses:</label>
                    <input type="file" id="file" name="file" accept=".csv" required>
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="detailed" name="detailed">
                        Include detailed validation results
                    </label>
                </div>
                <button type="submit">Upload and Validate</button>
            </form>
            <div id="status"></div>
        </div>
        
        <div class="api-info">
            <h3>API Endpoints</h3>
            <ul>
                <li><strong>POST /api/upload/</strong> - Upload CSV file for validation</li>
                <li><strong>GET /api/results/{job_id}</strong> - Download validation results</li>
                <li><strong>GET /api/status/{task_id}</strong> - Check task progress</li>
                <li><strong>GET /api/health</strong> - Health check</li>
            </ul>
            <p><strong>CSV Format:</strong> Your CSV file should have an 'email' column containing email addresses.</p>
        </div>

        <script>
            document.getElementById('uploadForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData();
                const fileInput = document.getElementById('file');
                const detailedInput = document.getElementById('detailed');
                
                formData.append('file', fileInput.files[0]);
                if (detailedInput.checked) {
                    formData.append('detailed', 'true');
                }
                
                const statusDiv = document.getElementById('status');
                statusDiv.innerHTML = '<div class="info">Uploading file...</div>';
                
                try {
                    const response = await fetch('/api/upload/', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        statusDiv.innerHTML = `
                            <div class="success">
                                <h4>Upload Successful!</h4>
                                <p>Job ID: ${result.job_id}</p>
                                <p>Task ID: ${result.task_id}</p>
                                <p>Status: ${result.status}</p>
                                <p>Check progress: <a href="/api/status/${result.task_id}" target="_blank">View Status</a></p>
                                <p>Download results when ready: <a href="/api/results/${result.job_id}" target="_blank">Download Results</a></p>
                            </div>
                        `;
                    } else {
                        statusDiv.innerHTML = `<div class="error">Error: ${result.detail}</div>`;
                    }
                } catch (error) {
                    statusDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
                }
            });
        </script>
    </body>
    </html>
    """

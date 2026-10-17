from fastapi import FastAPI
app = FastAPI(title='RecoNexus', version='0.1.0', description='Foundation only; persistent workflows are not yet implemented.')
@app.get('/health')
def health():
    return {'status': 'ok', 'database': 'not_configured', 'stage': 'domain_foundation'}

from fastapi.testclient import TestClient
from api_server import app

client = TestClient(app)
clin_path = 'testing datas/clinical_report.txt'
gut_path = 'testing datas/gut_microbiome_report.txt'
wear_path = 'testing datas/fitbit_wearable_report.txt'

with open(clin_path, 'rb') as f1, open(gut_path, 'rb') as f2, open(wear_path, 'rb') as f3:
    files = [
        ('files', ('clinical_report.txt', f1, 'text/plain')),
        ('files', ('gut_microbiome_report.txt', f2, 'text/plain')),
        ('files', ('fitbit_wearable_report.txt', f3, 'text/plain')),
    ]
    res_upload = client.post('/api/analyze', files=files)

contract2 = res_upload.json()[0]['mapper_output']
user_answers = {
    'Family_History_Diabetes': 'Yes',
    'Family_History_Hypertension': 'Yes',
    'Family_History_CVD': 'No',
}

res_assess = client.post(
    '/api/run-assessment',
    json={
        'contract2': contract2,
        'user_answers': user_answers,
        'patient_id': 'P001001',
    },
)

data = res_assess.json()
print('SCENARIO A RESULTS:')
for d in data['diseases']:
    k = d['key']
    r = d['risk_percentage']
    dec = d['decision']
    dt = d['decision_text']
    sl = d['status_label']
    print(f"  {k:22s} | risk={r}% | dec={dec} ({dt}) | status={sl}")

# Scenario B: Partial information (Gut + Wearable only)
with open(gut_path, 'rb') as f2, open(wear_path, 'rb') as f3:
    files = [
        ('files', ('gut_microbiome_report.txt', f2, 'text/plain')),
        ('files', ('fitbit_wearable_report.txt', f3, 'text/plain')),
    ]
    res_upload_b = client.post('/api/analyze', files=files)

contract2_b = res_upload_b.json()[0]['mapper_output']
res_assess_b = client.post(
    '/api/run-assessment',
    json={
        'contract2': contract2_b,
        'patient_id': 'P002002',
    },
)

data_b = res_assess_b.json()
print('\nSCENARIO B RESULTS:')
for d in data_b['diseases']:
    k = d['key']
    r = d['risk_percentage']
    dec = d['decision']
    dt = d['decision_text']
    sl = d['status_label']
    print(f"  {k:22s} | risk={r}% | dec={dec} ({dt}) | status={sl}")

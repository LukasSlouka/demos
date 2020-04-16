from firebase_admin import (
    firestore,
    initialize_app,
)

app = initialize_app()
fs_client = firestore.client(app=app)

for doc in fs_client.collection('breweries').stream():
    doc.reference.update({
        'name': 'flowup'
    })

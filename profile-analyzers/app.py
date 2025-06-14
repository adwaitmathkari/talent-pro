import os
import json
import faiss
import numpy as np
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from typing import List
from pdfminer.high_level import extract_text
from sentence_transformers import SentenceTransformer

# ----- CONFIG -----
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

SKILLS_MATRIX = [
  "Python", "Java", "JavaScript", "TypeScript", "Go", "Golang", "Rust", "C++", "C#", "Swift", "Kotlin", "Ruby", "Bash", "Shell scripting", "Scala", "R",
  "HTML5", "CSS3", "SCSS", "SASS", "React.js", "Angular", "Vue.js", "Svelte", "Next.js", "Tailwind CSS", "Webpack", "Vite", "Responsive Design", "Bootstrap", "Material UI", "WebAssembly", "WASM",
  "Node.js", "Express.js", "Spring Boot", "Django", "Flask", "FastAPI", ".NET Core", "NestJS", "GraphQL", "Apollo", "Relay", "RESTful APIs", "gRPC",
  "AWS", "Lambda", "S3", "EC2", "CloudFormation", "Azure", "App Services", "Functions", "AKS", "Google Cloud Platform", "GCP", "Docker", "Kubernetes", "Terraform", "Ansible", "Jenkins", "GitHub Actions", "GitLab CI", "Helm", "ArgoCD", "Vagrant",
  "SQL", "PostgreSQL", "MySQL", "SQLite", "NoSQL", "MongoDB", "DynamoDB", "Cassandra", "Redis", "Elasticsearch", "Neo4j", "Firebase", "Firestore", "InfluxDB",
  "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch", "Hugging Face Transformers", "OpenCV", "LangChain", "LLaMA", "Mistral", "GPT", "Claude", "Gemini", "MLflow", "Prompt Engineering", "FAISS", "Pinecone", "Weaviate", "Qdrant", "Apache Spark", "Dask", "Airflow", "dbt", "Kafka", "LLMOps",
  "Git", "GitHub", "GitLab", "Bitbucket", "JIRA", "Trello", "ClickUp", "Confluence", "Notion", "Agile", "Scrum",
  "OAuth 2.0", "OpenID Connect", "JWT", "OWASP Top 10", "Secure Coding Practices", "SIEM tools", "IAM", "Identity and Access Management",
  "Jest", "Mocha", "Chai", "Pytest", "unittest", "JUnit", "TestNG", "Cypress", "Playwright", "Selenium", "Postman", "Newman", "SonarQube", "TDD", "BDD",
  "React Native", "Flutter", "Dart", "Xamarin", "Ionic",
  "Solidity", "Ethereum", "EVM", "Hardhat", "Truffle", "IPFS", "Smart Contracts",
  "System Design", "API Design", "Documentation", "Clean Code", "SOLID principles", "Debugging", "Profiling", "Technical Writing", "Code Reviews"
]

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_DB_PATH = "faiss/resume_vector_index.faiss"
METADATA_PATH = "faiss/resume_metadata.json"

os.makedirs("faiss", exist_ok=True)

# Load model
model = SentenceTransformer(EMBEDDING_MODEL)

#################################### ----- CORE FUNCTIONS ----- ######################################
######################################################################################################
def extract_text_from_pdf(pdf_path: str) -> str:
    return extract_text(pdf_path)

def extract_skills(text: str, skill_set: List[str]) -> List[str]:
    text_lower = text.lower()
    return [skill for skill in skill_set if skill.lower() in text_lower]

def embed_resume_text(text: str) -> np.ndarray:
    return model.encode([text])[0]

def save_to_faiss(embedding: np.ndarray, metadata: dict):
    if os.path.exists(VECTOR_DB_PATH):
        index = faiss.read_index(VECTOR_DB_PATH)
        with open(METADATA_PATH, "r") as f:
            metadata_list = json.load(f)
    else:
        index = faiss.IndexFlatL2(len(embedding))
        metadata_list = []

    index.add(np.array([embedding]).astype("float32"))
    metadata_list.append(metadata)

    faiss.write_index(index, VECTOR_DB_PATH)
    with open(METADATA_PATH, "w") as f:
        json.dump(metadata_list, f, indent=2)

def query_similar_resumes(query_text: str, top_k=3):
    if not os.path.exists(VECTOR_DB_PATH) or not os.path.exists(METADATA_PATH):
        return []

    query_embedding = model.encode([query_text])[0]
    index = faiss.read_index(VECTOR_DB_PATH)

    with open(METADATA_PATH, "r") as f:
        metadata_list = json.load(f)

    D, I = index.search(np.array([query_embedding]).astype("float32"), top_k)
    return [metadata_list[i] for i in I[0] if i < len(metadata_list)]


####################################### ----- FLASK APP ----- #########################################
#######################################################################################################
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/upload', methods=['POST'])
def upload_resume():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    filename = secure_filename(file.filename)
    
    # Load existing metadata
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, "r") as f:
            metadata_list = json.load(f)
    else:
        metadata_list = []

    # Check for duplicate
    for entry in metadata_list:
        if entry.get("filename") == filename:
            return jsonify({'message': f'Resume "{filename}" already uploaded.', 'metadata': entry}), 409

    # Save the uploaded file
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)

    # Process
    text = extract_text_from_pdf(path)
    skills = extract_skills(text, SKILLS_MATRIX)
    embedding = embed_resume_text(text)
    metadata = {
        "filename": filename,
        "skills": skills,
        "length": len(text)
    }

    save_to_faiss(embedding, metadata)
    return jsonify({'message': 'Resume uploaded and embedded', 'metadata': metadata}), 200

@app.route('/search', methods=['GET'])
def search_resume():
    query = request.args.get('query', '')
    if not query:
        return jsonify({'error': 'Missing query param'}), 400
    results = query_similar_resumes(query)
    return jsonify({'query': query, 'results': results})


if __name__ == "__main__":
    app.run(debug=True)

# DissAssist – Inclusive Learning Assistance Platform



**An Assistive Learning Platform for Students with Dyslexia and Dysgraphia**



DissAssist is an inclusive learning assistance platform primarily designed to support students with Dyslexia and Dysgraphia. It provides accessible learning tools and interactive practice activities to help learners improve their reading, writing, spelling, speech, and overall learning experience.



Although the platform focuses on students with learning difficulties, it is also designed for children and learners of all abilities who want to improve their learning skills.



## 🎯 Project Objective



The main objective of DissAssist is to make learning more accessible, interactive, and supportive by providing digital tools that address common reading and writing challenges.



The platform aims to:

- Support students with Dyslexia and Dysgraphia.

- Improve reading and writing practice.

- Provide interactive spelling and grammar assistance.

- Encourage independent learning through accessible tools.

- Support children and general learners through skill-based practice.



## ✨ Key Features



### 1. Reading Assistance

- Reading practice and learning activities.

- Support for improving reading skills.



### 2. Handwriting Assistance

- Interactive handwriting practice.

- Handwriting analysis and feedback.

- Stroke-based assessment and recognition support.



### 3. Spelling and Grammar Assistance

- Spelling checker.

- Grammar checking and suggestions.

- Language improvement support.



### 4. Speech Assistance

- Speech practice activities.

- Speech-to-text and text-to-speech support.



### 5. Learning Dashboard

- Student dashboard.

- Guardian dashboard.

- Student management and profile features.



### 6. Accessibility Support

- Accessibility-focused interface.

- Interactive learning experience.

- Tools designed to support different learning needs.



## 🛠️ Technology Stack



| Category | Technologies |

|---|---|

| Backend | Python, Flask |

| Frontend | HTML, CSS, JavaScript |

| Database | SQLite, Flask-SQLAlchemy |

| Image Processing | Pillow, NumPy |

| Spelling \& Grammar | PySpellChecker, LanguageTool API |

| Speech Features | Browser Speech APIs |



## 📂 Project Structure



```text

DissAssist/

│

├── app.py

├── config.py

├── extensions.py

├── models.py

├── requirements.txt

├── seed\_data.py

│

├── static/

│   ├── css/

│   └── js/

│

├── templates/

│

├── utils/

│   ├── grammar\_check.py

│   ├── handwriting\_check.py

│   └── recommendations.py

│

├── .gitignore

└── README.md

```



## ⚙️ Installation and Setup



### Prerequisites



- Python 3.10 or later

- Git

- pip (Python package manager)



### Step 1: Clone the Repository



```bash

git clone https://github.com/gokulhari-r/DissAssist.git

```



### Step 2: Navigate to the Project Folder



```bash

cd DissAssist

```



### Step 3: Create a Virtual Environment



```bash

python -m venv venv

```



### Step 4: Activate the Virtual Environment



**Windows:**



```bash

venv\\Scripts\\activate

```



### Step 5: Install Dependencies



```bash

pip install -r requirements.txt

```



### Step 6: Run the Application



```bash

python app.py

```



Open the local URL displayed in your terminal to access the application.



## 🔐 Configuration



The application supports environment-based configuration.



For deployment, configure a secure `SECRET\_KEY` and an appropriate `DATABASE\_URL` using environment variables.



Never commit private credentials or production secrets to GitHub.



## 🌱 Future Enhancements



- Advanced AI-powered personalized learning assistance.

- Improved handwriting recognition and analysis.

- Personalized learning recommendations.

- More interactive educational activities.

- Enhanced accessibility features.

- Progress tracking and learning analytics.



## 👥 Target Users



- Students with Dyslexia.

- Students with Dysgraphia.

- Children developing reading and writing skills.

- Teachers and guardians.

- General learners seeking additional learning support.



## 📌 Project Information



**Project Name:** DissAssist



**Project Category:** Assistive Technology / EdTech



**Primary Focus:** Inclusive Learning Assistance



**Developer:** Gokulhari Rajkumar



**GitHub Repository:** https://github.com/gokulhari-r/DissAssist



---



*DissAssist aims to make learning more accessible, inclusive, and supportive for everyone.*



\*\*Learning without barriers. Growing without limits.\*\*


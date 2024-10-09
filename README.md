# Learning Application for Year 3-4 Students

This project is a learning application designed for Year 3-4 students to help them practice basic numeracy skills.

---

## <u>Features</u>

- **Immediate Feedback**
- **Progress Tracking**: Records results following attempts in a CSV file.
- **Cross-Platform**: Runs as a standalone desktop app. This app works on Windows, macOS, Linux and Android when run in python, although it has only been tested on Windows and macOS. It is recommended this app only runs on Windows and macOs.

---

## <u>Prerequisites</u>

- [Python 3.6+](https://www.python.org/downloads/)
- [Pip](https://pip.pypa.io/en/stable/installation/)
- [Git  (optional)](https://git-scm.com/downloads)
- Other prerequisites (e.g., Flask, PyWebview, etc.) are downloaded in "Installation".

---

## <u>Installation</u>
### Setup for **Windows** and **macOS**

Either use the **unzipped folder** method or **clone via Git**.

### Option 1: Using the Unzipped Folder

1. **Download** the project as a zip file from the source repository.  
2. **Unzip** the file into your desired directory.

### Option 2: Cloning the Repository

1. Open a terminal (Command Prompt for Windows, Terminal for macOS).  
2. Run the following command to clone the repository (replace `repo-url` with the actual repository URL):  
     
   ```bash  
   git clone \<repo-url\>  
   ```
## Environment Setup

Follow the steps below to set up the environment, install prerequisites, and run the application.

## 3\. Set Up a Virtual Environment (optional)

- **Windows:**  
    
  Open Command Prompt and navigate to the project directory (replace `project-folder` with the name of the folder from the cloned repo):  
    
  ```bash  
  cd \<project-folder\>  
    
  python \-m venv venv  
    
  venv\\Scripts\\activate  
  ```  
    
- **macOS:**  
    
  Open Terminal and navigate to the project directory (replace `project-folder` with the name of the folder from the cloned repo):  
    
  ```bash  
  cd \<project-folder\>  
    
  python3 \-m venv venv  
    
  source venv/bin/activate  
  ```

### 4\. Install Dependencies

Install the required packages which are specified in the `requirements.txt` file. If you followed step 3, these won't be installed globally but rather in the virtual environment.

```bash  
pip install \-r requirements.txt  
```  
---

### 5\. Run the Application

To run the application, run the following command:

```bash  
python app.py  
```  
---

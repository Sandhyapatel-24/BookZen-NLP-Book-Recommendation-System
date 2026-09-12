# BookZen-NLP-Book-Recommendation-System
BookZen – An NLP-based book recommendation and genre classification system using TF-IDF, Cosine Similarity and Logistic Regression

# 📚 BookZen: NLP-Based Book Recommendation and Genre Classification System

BookZen is an NLP-based web application that helps users discover books based on their interests. It provides personalized book recommendations and automatically predicts the genre of a book using its description.

## 🚀 Features

- 🔐 User Registration and Login
- 📖 Book Search and Exploration
- 🤖 NLP-based Book Recommendation
- 🎯 Genre Prediction
- ❤️ Add Books to Favorites
- 📊 Recommendation History
- 🛠️ Admin Login and Dashboard
- 📚 Manage Books
- ➕ Add New Books
- ✏️ Edit Book Details
- 🗑️ Delete Books

## 🧠 Technologies Used

- Python
- Flask
- Natural Language Processing (NLP)
- Scikit-learn
- TF-IDF
- Cosine Similarity
- Logistic Regression
- SQLite
- HTML
- CSS
- JavaScript
- Jupyter Notebook

## 🔍 Recommendation System

BookZen uses **TF-IDF (Term Frequency-Inverse Document Frequency)** to convert book descriptions into numerical vectors.

**Cosine Similarity** is then used to measure the similarity between books. Books with higher similarity scores are recommended to the user.

### Recommendation Workflow

1. User selects or searches for a book.
2. The book description is processed.
3. TF-IDF converts the description into numerical features.
4. Cosine Similarity calculates similarity with other books.
5. The most relevant books are recommended.

## 🎯 Genre Classification

BookZen uses **TF-IDF features with Logistic Regression** to predict the genre of a book from its description.

### Example

**Input:**
> A young wizard discovers a magical kingdom and must fight an ancient dark force.

**Predicted Genre:**
> Fantasy

## 📊 Machine Learning Models

Three classification models were evaluated:

| Model | Accuracy |
|-------|----------|
| Multinomial Naive Bayes | 97.92% |
| Logistic Regression | 100% |
| Linear SVM | 100% |

Logistic Regression was selected as the final genre classification model because it achieved 100% accuracy and works effectively with TF-IDF features.

## 📂 Project Structure

```text
BookZen/
│
├── app.py
├── BookZen.ipynb
├── bookzen_books_1200_realistic.csv
├── bookzen_genre_model.pkl
├── bookzen_tfidf_vectorizer.pkl
├── bookzen.db
│
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── admin_login.html
│   ├── admin_dashboard.html
│   └── ...
│
└── static/
    ├── css/
    └── js/


▶️ How to Run
1. Clone the Repository
git clone https://github.com/YOUR-USERNAME/BookZen-NLP-Book-Recommendation-System.git
2. Open the Project
cd BookZen-NLP-Book-Recommendation-System
3. Install Dependencies
pip install flask pandas numpy scikit-learn joblib
4. Run the Application
python app.py

Open the application in your browser:

http://127.0.0.1:5000/
👩‍💻 Project

BookZen – An NLP-Based Book Recommendation and Genre Classification System

Developed as an academic mini project using Natural Language Processing and Machine Learning.

📜 License

This project is developed for educational and academic purposes.


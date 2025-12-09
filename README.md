# 📊 Instagram Analytics – Data Science Project

## 📌 Project Overview

This project is an end-to-end **data science and machine learning analysis** of Instagram performance data. The objective is to explore, clean, visualise, and model engagement metrics in order to understand what drives content performance on Instagram.

This repository demonstrates practical skills in:

* Data cleaning and preprocessing
* Exploratory Data Analysis (EDA)
* Data visualisation
* Feature engineering
* Machine learning model building
* Interpreting results and drawing conclusions

The project is designed as a **portfolio showcase** for junior data science / Python roles.

---

## 📂 Dataset

**Source:** Kaggle
**Dataset name:** Instagram Analytics Dataset
**Author:** Kundan Bedmutha

🔗 Dataset link:
[https://www.kaggle.com/datasets/kundanbedmutha/instagram-analytics-dataset?select=Instagram_Analytics.csv](https://www.kaggle.com/datasets/kundanbedmutha/instagram-analytics-dataset?select=Instagram_Analytics.csv)

The dataset contains information about Instagram posts including engagement metrics, reach, impressions, content type, and posting date.

---

## 🧾 Columns Overview

Key columns used in this project include:

* `upload_date` – Date the post was uploaded
* `media_type` – Type of media (image, reel, video)
* `content_category` – Category of the post content
* `likes`, `comments`, `shares`, `saves`
* `reach`, `impressions`
* `followers_gained`
* `engagement_rate`
* `hashtags_count`
* `caption_length`

---

## 🧼 Data Cleaning & Preparation

The following steps were applied:

* Converted `upload_date` to datetime format
* Verified there were no missing values
* Created new time-based features:

  * `upload_month`
  * `upload_day`
* Selected relevant numeric features for machine learning

---

## 📈 Exploratory Data Analysis & Visualisations

The analysis includes multiple visual insights:

1. **Average Engagement Rate by Media Type**
   Used to compare how different content formats perform.

2. **Reach vs Likes Scatter Plot**
   Explores the relationship between visibility and engagement.

3. **Followers Gained by Content Category**
   Highlights which content types are most effective at audience growth.

Visualisations were created using **Matplotlib** and **Seaborn**.

---

## 🤖 Machine Learning

### Objective

Predict **engagement rate** based on post characteristics.

### Model Used

* **Linear Regression** (for simplicity and interpretability)

### Features

* Likes
* Comments
* Shares
* Saves
* Reach
* Impressions
* Caption length
* Hashtags count

### Evaluation Metrics

* **R² Score**
* **Root Mean Squared Error (RMSE)**

Feature coefficients were analysed to understand which variables most strongly influence engagement.

---

## ✅ Key Insights

* Engagement is influenced by multiple metrics, not just likes
* Reels and videos generally achieve higher engagement rates
* Saves and reach play a strong role in engagement prediction
* Some content categories are more effective for gaining followers

---

## 🚀 Future Improvements

* Convert the problem into a classification task (high vs low engagement)
* Apply more advanced models (Random Forest, XGBoost)
* Perform time-based analysis on posting trends
* Deploy as an interactive dashboard (Streamlit)

---

## 🛠️ Tools & Technologies

* Python
* Pandas, NumPy
* Matplotlib, Seaborn
* Scikit-learn
* Jupyter Notebook

---

## 👤 Author

This project was created as part of a personal learning journey in **data science and Python programming**, and serves as a portfolio piece to demonstrate practical analytics and machine learning skills.


---

⭐ If you found this project interesting, feel free to star the repository!

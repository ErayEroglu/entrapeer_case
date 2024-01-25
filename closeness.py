import nltk # pip install nltk
from sklearn.feature_extraction.text import TfidfVectorizer # pip3 install -U scikit-learn
import json
import numpy as np

from print_schema import print_schema
import seaborn as sns  # pip install seaborn

from scipy.spatial.distance import squareform
from scipy.cluster.hierarchy import dendrogram, linkage
from matplotlib import pyplot as plt # pip install matplotlib
from scipy.cluster.hierarchy import fcluster

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

from sklearn.metrics.pairwise import cosine_similarity
lemmatizer = WordNetLemmatizer()

def set_diagonal_to_zero(matrix):
    np.fill_diagonal(matrix, 0)
    return matrix

def set_diagonal_to_one(matrix):
    np.fill_diagonal(matrix, 1)
    return matrix

def preprocess(text):
    text = text.lower()
    word_list = nltk.word_tokenize(text)
    word_list = [lemmatizer.lemmatize(word) for word in word_list if word not in stopwords.words('english') and word.isalnum()]
    return ' '.join(word_list)

def get_description_closeness(companies):
    descriptions = [company['description'] for company in companies]    

    tfidf_vectorizer = TfidfVectorizer(preprocessor=preprocess)
    tfidf_matrix = tfidf_vectorizer.fit_transform(descriptions) # 'documents' is a list of all company descriptions
    
    cosine_sim = cosine_similarity(tfidf_matrix)
    # print(cosine_sim)
    return cosine_sim

def get_geo_closeness(companies):
    num_companies = len(companies)
    geo_closeness_matrix = np.zeros((num_companies, num_companies))

    for i, company in enumerate(companies):
        for j, other_company in enumerate(companies):
            if i != j:
                if company['hq_country'] == other_company['hq_country']:
                    if company['hq_city'] == other_company['hq_city']:
                        geo_closeness_matrix[i][j] = 1  # Same city
                    else:
                        geo_closeness_matrix[i][j] = 0.5  # Same country, different city
                else:
                    geo_closeness_matrix[i][j] = 0  # Different countries
    # print(geo_closeness_matrix)
    return geo_closeness_matrix  

def get_same_partners_closeness(companies):
    num_companies = len(companies)
    partner_closeness_matrix = np.zeros((num_companies, num_companies))

    # Mapping from company ids to array indexes for the partner closeness matrix
    company_index = {company['id']: idx for idx, company in enumerate(companies)} # putting the company id instead of indexes

    # Populate the partner closeness matrix
    for company in companies:
        current_company_index = company_index[company['id']]
        current_company_partners = set(partner['master_startup_id'] for partner in company['startup_partners'])
        
        for other_company in companies:
            other_company_index = company_index[other_company['id']]
            if current_company_index != other_company_index:
                other_company_partners = set(partner['master_startup_id'] for partner in other_company['startup_partners'])
                
                # Calculate the shared and combined partners
                shared_partners = current_company_partners.intersection(other_company_partners)
                combined_partners = current_company_partners.union(other_company_partners)
                
                # Normalization
                if len(combined_partners) > 0:
                    partner_closeness_matrix[current_company_index][other_company_index] = len(shared_partners) / len(combined_partners)
                else:
                    partner_closeness_matrix[current_company_index][other_company_index] = 0

    # print(partner_closeness_matrix)
    return partner_closeness_matrix

def calculate_theme_similarity(company1, company2):
    # Themes for each company which is linked to the count of partners with that theme
    themes1 = {theme[0]: int(theme[1]) for theme in company1['startup_themes']}
    themes2 = {theme[0]: int(theme[1]) for theme in company2['startup_themes']}
    

    # Find shared themes and all themes
    shared_themes = set(themes1).intersection(set(themes2))
    total_themes = set(themes1).union(set(themes2))
    
    # Calculate similarity score based on shared themes and their counts
    similarity_score = sum(min(themes1[theme], themes2[theme]) for theme in shared_themes)
    # Calculate maximum possible score also gives the total number of partners
    max_score = sum(themes1.get(theme, 0) + themes2.get(theme, 0) for theme in total_themes)  # Used get() to avoid KeyError


    # Normalize to a value between 0 and 1
    if max_score > 0:
        normalized_score = similarity_score / max_score
    else:
        normalized_score = 0
    
    return normalized_score

def get_theme_closeness(companies):
    num_companies = len(companies)
    theme_closeness_matrix = np.zeros((num_companies, num_companies))
    count = 0
    for i in range(num_companies):
        # print(count)
        # count += 1
        for j in range(i+1, num_companies):  
            similarity = calculate_theme_similarity(companies[i], companies[j])
            theme_closeness_matrix[i][j] = similarity
            theme_closeness_matrix[j][i] = similarity # since the matrix is symmetric 
    
    return theme_closeness_matrix

def get_partner_closeness(companies):
    same_partner_matrix = get_same_partners_closeness(companies)
    similar_theme_partner_matrix = get_theme_closeness(companies)

    return same_partner_matrix , similar_theme_partner_matrix


def combine_matrices(description_matrix, geo_matrix, partner_matrix, theme_matrix):

    # Importance levels for each matrix
    description_importance = 3
    geo_importance = 1
    partner_importance = 5
    theme_importance = 4

    combined_matrix = (description_importance * description_matrix + geo_importance * geo_matrix + partner_importance * partner_matrix + theme_importance * theme_matrix) / (description_importance + geo_importance + partner_importance + theme_importance)

    return combined_matrix

def hierarchical_clustering(combined_matrix):
    linked = linkage(combined_matrix, 'single')
    plt.figure(figsize=(10, 7))
    dendrogram(linked, orientation='top', distance_sort='descending', show_leaf_counts=True)
    plt.show()

def create_clusters(combined_matrix, num_clusters):
    linked = linkage(combined_matrix, 'complete') # 'single', 'complete', 'average', 'weighted', 'centroid', 'median', 'ward'
    cluster_labels = fcluster(linked, num_clusters, criterion='maxclust')
    return cluster_labels

def heatmap(combined_matrix):
    # Generate and save the heatmap
    plt.figure(figsize=(10, 10))  # You can adjust the size of the figure
    sns.heatmap(combined_matrix, cmap='viridis')  # 'viridis', 'plasma', 'inferno', 'magma', 'cividis' are some good colormaps
    plt.title('Combined Matrix Heatmap')
    plt.savefig('combined_matrix_heatmap.png')  # Save the figure
    plt.show()  # Display the figure

def grouper(companies):
    description_matrix = set_diagonal_to_zero(get_description_closeness(companies))
    geo_matrix = get_geo_closeness(companies)
    partner_matrix, theme_matrix = get_partner_closeness(companies)
    combined_matrix = combine_matrices(description_matrix, geo_matrix, partner_matrix, theme_matrix)

    # combined_matrix = set_diagonal_to_one(combined_matrix)
    # print(combined_matrix)

    # heatmap(combined_matrix[:20, :20])
    # hierarchical_clustering(combined_matrix)
    
    num_clusters = 20 # You can decide this number based on the dendrogram
    cluster_labels = create_clusters(combined_matrix, num_clusters)

    # Prepare the data for JSON serialization
    for i, company in enumerate(companies):
        company['clusterNo'] = int(cluster_labels[i])  # Convert Numpy int to Python int
        # company['matrix'] = combined_matrix[i].tolist()  # Convert Numpy array to list

    for i in range(1, num_clusters + 1):
        print(f'Cluster {i}:')
        print([company['name'] for company in companies if company['clusterNo'] == i])

    # for i, company in enumerate(companies):
    #     print(i, company['clusterNo'])

    
    return companies, num_clusters

if __name__ == '__main__':
    # Path to your JSON file
    file_path = 'company_details.json'
    
    # Reading the JSON data from the file
    with open(file_path, 'r') as file:
        companies = json.load(file)
    
    grouper(companies)
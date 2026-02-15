"""
Script to preload subject data into the RAG vector store.
Run this to initialize your knowledge base.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.rag.subject_rag import get_rag


# Sample subject content - you can load from files or databases
SUBJECT_DATA = {
    "Machine Learning": """
    Machine Learning is a subset of artificial intelligence that enables systems to learn from data.
    
    Supervised Learning: Algorithms learn from labeled data. Examples include:
    - Linear Regression: Predicts continuous values
    - Logistic Regression: Binary classification
    - Decision Trees: Tree-based models for classification/regression
    - Random Forest: Ensemble of decision trees
    - Support Vector Machines: Finds optimal hyperplane
    - Neural Networks: Multi-layer perceptrons
    
    Unsupervised Learning: Finds patterns in unlabeled data:
    - K-Means Clustering: Groups similar data points
    - Hierarchical Clustering: Creates tree of clusters
    - Principal Component Analysis: Dimensionality reduction
    - Autoencoders: Neural networks for representation learning
    
    Reinforcement Learning: Agents learn through interaction:
    - Q-Learning: Value-based learning
    - Policy Gradients: Direct policy optimization
    - Deep Q Networks: Deep learning for Q-learning
    
    Key Concepts:
    - Overfitting: Model learns noise in training data
    - Underfitting: Model too simple to capture patterns
    - Cross-validation: Splitting data for validation
    - Bias-Variance Tradeoff: Balance between simplicity and complexity
    - Gradient Descent: Optimization algorithm
    - Backpropagation: Training neural networks
    """,
    
    "Deep Learning": """
    Deep Learning uses neural networks with multiple layers.
    
    Neural Network Architectures:
    - Feedforward Neural Networks: Basic architecture
    - Convolutional Neural Networks (CNN): For image data
    - Recurrent Neural Networks (RNN): For sequential data
    - Long Short-Term Memory (LSTM): Advanced RNN
    - Transformers: Attention-based architecture
    - Generative Adversarial Networks (GAN): Generate new data
    
    Activation Functions:
    - ReLU: f(x) = max(0, x)
    - Sigmoid: f(x) = 1/(1+e^{-x})
    - Tanh: f(x) = tanh(x)
    - Softmax: For multi-class classification
    
    Training Techniques:
    - Batch Normalization: Normalize layer inputs
    - Dropout: Prevent overfitting
    - Learning Rate Scheduling: Adjust learning rate
    - Weight Initialization: Proper weight initialization
    
    Applications:
    - Computer Vision: Image classification, object detection
    - Natural Language Processing: Text classification, translation
    - Speech Recognition: Audio to text
    - Reinforcement Learning: Game playing, robotics
    """,
    
    "Natural Language Processing": """
    NLP enables computers to understand human language.
    
    Text Processing:
    - Tokenization: Splitting text into tokens
    - Stemming: Reducing words to root form
    - Lemmatization: Dictionary-based root form
    - Stop Words: Removing common words
    - Part-of-Speech Tagging: Identifying word types
    
    Word Embeddings:
    - Word2Vec: Word vectors from context
    - GloVe: Global vectors for word representation
    - FastText: Subword information
    - BERT: Contextual embeddings
    - GPT: Generative pre-training
    
    NLP Tasks:
    - Text Classification: Categorizing text
    - Named Entity Recognition: Identifying entities
    - Sentiment Analysis: Determining sentiment
    - Machine Translation: Translating languages
    - Question Answering: Answering questions
    - Text Generation: Generating text
    
    Advanced Models:
    - Transformers: Attention is all you need
    - BERT: Bidirectional Encoder Representations
    - GPT: Generative Pre-trained Transformer
    - T5: Text-to-Text Transfer Transformer
    """,
    
    "Computer Vision": """
    Computer Vision enables machines to interpret visual data.
    
    Image Processing:
    - Filtering: Gaussian, median filters
    - Edge Detection: Canny, Sobel operators
    - Feature Detection: SIFT, SURF, ORB
    - Image Segmentation: Thresholding, clustering
    
    CNN Architectures:
    - LeNet: Early CNN for digit recognition
    - AlexNet: Deep CNN for ImageNet
    - VGG: Very deep convolutional networks
    - ResNet: Residual networks
    - Inception: GoogLeNet architecture
    - EfficientNet: Optimized scaling
    
    Vision Tasks:
    - Image Classification: Categorizing images
    - Object Detection: Finding and classifying objects
    - Semantic Segmentation: Pixel-level classification
    - Instance Segmentation: Individual object segmentation
    - Image Generation: GANs, VAEs
    - Style Transfer: Applying artistic styles
    
    Applications:
    - Facial Recognition: Identifying faces
    - Autonomous Vehicles: Scene understanding
    - Medical Imaging: Disease detection
    - Augmented Reality: Overlaying digital content
    """
}


def load_sample_data():
    """Load sample subject data into RAG."""
    print("Loading sample data into RAG...")
    
    rag = get_rag()
    
    for subject, content in SUBJECT_DATA.items():
        print(f"Adding {subject}...")
        success = rag.add_subject_content(
            subject=subject,
            content=content,
            source="sample_data"
        )
        if success:
            print(f"✅ Added {subject}")
        else:
            print(f"❌ Failed to add {subject}")
    
    print("\nRAG Statistics:")
    stats = rag.get_stats()
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    import json
    load_sample_data()
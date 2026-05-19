\title{
varMax: Uncertainty and Novelty Management in Deep Neural Networks
}

\author{
Alexandre Broggi \\ University of Massachusetts Dartmouth \\ abroggi@umassd.edu \\ Nicholas Costagliola \\ University of Massachusetts Dartmouth \\ ncostagliola@umassd.edu
}

\author{
Gaspard Baye \\ University of Massachusetts \\ Dartmouth \\ bgaspard@umassd.edu \\ Nathaniel Bastian \\ US Military Academy \\ nathaniel.bastian@westpoint.edu
}

\author{
Priscila Silva \\ University of Massachusetts \\ Dartmouth \\ psilva4@umassd.edu
}

\author{
Gokhan Kul \\ University of Massachusetts Dartmouth \\ gkul@umassd.edu
}

\begin{abstract}
Traditional Deep Neural Networks often struggle with new or unfamiliar data patterns since they operate on a closed-set assumption. This challenge arises due to inherent limitations in the model architecture, such as the softmax function commonly used for classification tasks, which tends to exhibit overconfidence and inaccuracies when faced with novel inputs. Prior studies have highlighted the need for open-set recognition (OSR) techniques to differentiate between known and unknown data points, but existing approaches often exhibit a bias toward flagging inputs as unknown. To address this issue, we introduce a novel OSR technique called VarMax, designed to maintain a balanced approach. VarMax leverages the variance in model predictions to discern between known and unknown inputs. We propose a method for classifying ambiguous samples based on prediction variance to detect out-of-distribution samples to enhance classification accuracy and reliability. Our experiments demonstrate that VarMax meets and exceeds the performance of existing methods in identifying unknown data points while also improving the model's confidence and robustness in distinguishing between known and unknown inputs.
\end{abstract}

Keywords: Deep neural networks, open-set recognition, uncertainty management

\section*{1. Introduction}

Deep neural networks (DNNs) have been successfully deployed to perform various classification tasks across academia and production environments, such as medical imaging (Tunnell et al., 2022),
anomaly detection (Baye et al., 2021), and network intrusion detection (Ahmad et al., 2021). Their notable accuracy and F-1 scores across different data classes highlight their potential in a wide range of applications. Despite these advancements, DNNs face a fundamental challenge (Shafiq and Gu, 2022): their closed-set nature makes them less effective at handling changing characteristics and samples that exhibit previously unknown features. This limitation arises from DNNs' reliance on the SoftMax function in their final layer, which leads to overconfident classifications of unseen data into known categories, resulting in false predictions (Wang et al., 2021).

Various open-set recognition (OSR) algorithms have been developed (Hassen and Chan, 2020; Liu et al., 2020; Shu et al., 2017) to replace the SoftMax in determining whether a sample belongs to a class within the training set. These algorithms, however, were initially designed and proposed for image data (Khosla and Gangadharaiah, 2022; Wang et al., 2021), namely, samples in $n \times m$ form.

We aim to ensure that previously unknown samples are neither overlooked due to misplaced confidence, nor known samples excessively flagged as unknowns. This paper proposes a novel methodology that addresses the limitations of traditional softmax-based DNNs and OSR algorithms. Our approach employs a bias-neutral strategy specifically developed to identify unknown samples, which could represent either benign novel activities or previously unseen anomalies. This approach is designed to enhance the DNN's ability to recognize and accurately classify unknown patterns, thereby improving the overall robustness of critical systems against emerging challenges. Through analytical evaluations, we demonstrate that
our methodology addresses the biases inherent in existing detection methods and offers a new reliability benchmark for integrating DNNs into various real-world applications.

This paper presents a novel approach for classifying vector inputs into known and unknown categories. Our methodology consists of two main stages. Initially, we calculate the softmax probabilities $P$ (AUEB et al., 2016) for the input classes, with particular attention to the difference $\Delta$ between the top-ranked class probability $P_{1}$ and the second-ranked class probability $P_{2}$. A small $\Delta$ suggests uncertainty in the input classification (Berenbeim et al., 2023). To address this uncertainty, we introduce VarMax, a technique that evaluates the variance $\sigma^{2}$ (Larson, 2008) in the DNN's logits. This analysis generates a variance confidence score crucial for differentiating known inputs, showing higher variance $\sigma_{\text {high }}^{2}$, from unknown ones, showing lower variance $\sigma_{\text {low }}^{2}$. We also show the effectiveness of VarMax with comparisons to one of the most well-known OSR end-layers, energy-based out-of-distribution (OOD) algorithm (Liu et al., 2020).

Our methodology improves the accuracy in classifying known and unknown inputs and provides a systematic method to categorize them effectively in an open-set setting. Concretely, the primary contributions of this work are as follows. (i) We enhance the capability of softmax from a closed-set framework to an open-set one by pinpointing and addressing classification uncertainties. This is achieved by introducing the top two differences, where we compute the difference between the top two probabilities obtained from softmax scores to determine if the predictions are certain or ambiguous. (ii) To boost the confidence of this process, we propose VarMax, a technique that evaluates variances in DNN logits to develop a variance confidence score. This score differentiates between known inputs, characterized by higher variance, and unknown inputs, which exhibit lower variance. Lastly, we carried out comprehensive experiments using standard benchmark datasets to showcase that VarMax significantly improves the detection of unknown samples, particularly vectors.

The paper is organized as follows. The related works and background are presented in §2. We will lay out the VarMax hypothesis in §3. We then delve into the experiments in §4. We discuss hybrid approaches in §5. We conclude and express our thoughts on possible future work in §6. Our experimentation code and links to the datasets are shared publicly along with reproducibility instructions are shared publicly here ${ }^{1}$.

\footnotetext{
${ }^{1}$ https://github.com/PADLab/varMax-HICSS
}

\section*{2. Literature Review}

OSR addresses the challenge where new, unknown classes, which were not present during the training phase, emerge during testing (Scheirer et al., 2012). This necessitates that classifiers be adept not only at precisely recognizing established classes but also at effectively managing classes that are newly encountered. Consequently, it is essential for these classifiers to incorporate a rejection mechanism for instances that belong to these unknown categories. Figure 1 visualizes the process executed by an open-set classifier, which includes the identification of unknown classes while simultaneously classifying known ones. Definition 1 describes the OSR algorithm, accompanied by a scenario that demonstrates its practical application.
Definition 1 Consider positive training data represented by samples $X^{+}=\left\{x_{1}, \ldots, x_{m}\right\}$ drawn from distribution $P$, and negative training data samples $X^{-}=\left\{n_{1}, \ldots, n_{l}\right\}$ from known classes $N$. Let $W$ denote the expansive set of potential unknown (negative) classes that only emerge during testing, and define the test data set as $Y=\left\{y_{1}, \ldots, y_{p}\right\}$, where $y_{i} \in P \cup N \cup W$, and the openness of the problem is greater than zero.

Given the training data $X^{+} \cup X^{-}$, an open space risk function $R_{O}$, and an empirical risk function $R_{E}$, the goal of OSR is to identify a measurable recognition function $g \in G$, where $g(x)>0$ indicates positive recognition. This function $g$ is determined by minimizing the Open-Set Risk:

$$
\operatorname{argmin}_{g \in G} R_{O}(g)+\lambda R_{E}\left(g\left(X^{+} \cup X^{-}\right)\right),
$$

where $\lambda$ is a regularization parameter. In this formulation, OSR is defined as the minimization of open-set risk, which is a combination of the open space risk and empirical risk, across the spectrum of permissible recognition functions. Considering the properties of the function $g \in G$, this definition effectively balances the known elements from $X^{+} \cup X^{-}$, and the open space risk $R_{O}$ associated with the unknown classes $W$.

The remarkable achievements of DNNs have led to their widespread application across various domains despite concerns regarding the accuracy of their predictions (Guo et al., 2017; Hsu et al., 2020; LeCun et al., 2006; Padhy et al., 2020; Wang et al., 2021), particularly in identifying unfamiliar inputs that the model has never encountered. Ensuring that these networks accurately calibrate their confidence levels is crucial for producing authentic representations of their predictions for both known and unknown inputs, especially in the context of network intrusion detection.

\begin{figure}
\includegraphics[alt={},max width=\textwidth]{https://cdn.mathpix.com/cropped/82a9a401-c001-46bd-9883-ce8261a5df26-03.jpg?height=297&width=759&top_left_y=232&top_left_x=266}
\captionsetup{labelformat=empty}
\caption{Figure 1: An ideal DNN is able to classify what it knows correctly and identify what it does not know. The unknown sample can then be sent into other tools for further analysis, recognition, or labeling}
\end{figure}

The importance of this stems from the potential for unreliable predictions to incorrectly classify unknown, potentially harmful attacks, including zero-days, as harmless traffic. This misclassification could ultimately compromise the network's security (Elmasry et al., 2019). Thus, it's imperative to accurately assess the confidence with which a DNN can determine whether an input is previously known or novel.

Consequently, previous research suggests various methods to achieve confidence scaling (Mandelbaum and Weinshall, 2017). Specifically, Wang et al., 2021 formulated their uncertainty calibration through an energy-based (Grathwohl et al., 2019; Liu et al., 2020; Padhy et al., 2020) approach. These researchers presented a unique $K+1$ way softmax model, which includes an extra dimension to account for open-world uncertainty. This integration of the additional dimension with the conventional K-way classification task led to two primary innovations: (i) a unique energy-based objective function, and (ii) a theoretical framework that proves optimizing this function successfully ensures that the extra dimension captures the marginal data distribution. Their findings indicate that this Energy-based Open-World Softmax (EOW-Softmax) approach surpasses existing leading methods for improving confidence calibration.

A prevalent technique in this field is known as temperature scaling (Guo et al., 2017; Hsu et al., 2020; Liang et al., 2017). This approach integrates a scaling factor (temperature) into the softmax equation. The primary objective of this modification is to refine the softmax probabilities, making them more tempered or moderated. This adjustment is typically conducted on a validation set to achieve optimal calibration of the probabilities. Other regularization methods, including label smoothing (Szegedy et al., 2016) and mixup (Thulasidasan et al., 2019), have also shown efficacy in enhancing the calibration process. Specifically, label smoothing alters the actual labels by blending them with a uniform distribution, compelling neural networks
to generate more leveled probability outputs. On the other hand, Mixup is an approach to data augmentation that combines two different instances in both the image and label domains, incidentally resulting in enhanced calibration. However, in zero-day attack detection, the precision and clarity of distinguishing between known and unknown attack classes are paramount. Methods like Mixup, which blends instances, and label smoothing, which alters labels, could blur these critical distinctions, undermining the effectiveness of our detection system. Therefore, their use is incompatible with our project's emphasis on preserving the specificity and integrity of the data.

Farrukh et al., 2023 introduces image-based representations of packet-level data for detecting unknown attacks. Though promising, its integration into existing security systems could face challenges, particularly with necessary adjustments to data handling processes, potentially affecting real-world adoption and effectiveness. We also have Matejek et al., 2024, which employs a generative model for uncertainty quantification, and Wong et al., 2023 contrasts deterministic models with computationally demanding Bayesian neural networks, estimated through Hamiltonian Monte Carlo using a NIDS dataset. While promising, both methods are complex and face significant computational challenges, with the generative model and Bayesian networks requiring extensive processing power due to complex sampling processes. These computational demands highlight the primary hurdles associated with deploying these advanced techniques in practical settings.

The literature shows significant progress in enhancing confidence calibration within deep neural networks. However, most methods for measuring this confidence have been tailored to computer vision tasks and tested with image-based datasets. Network intrusion detection involves a very different kind of data characterized by distinct patterns and features not found in images. As a result, while these methods may work well for images, our research (Baye et al., 2023) suggests that their effectiveness often decreases when applied to detecting unknown activities in network security. Furthermore, methods employing network intrusion detection system data often significantly complicate data preparation or demand extensive computational resources.

In our experiments, for comparison, we use the energy-based function by Liu et al., 2020, which introduced a method that employs energy scores for OOD sample detection, proving them superior to traditional Softmax scores in distinguishing between in-distribution and OOD samples. Energy scores, less
prone to overconfidence than softmax, are more closely related to the probability density of inputs. This technique enables using energy scores as an evaluative tool for existing neural classifiers and as an adaptable function to refine OOD detection capabilities. The energy-based function for OOD detection is defined as:

$$
E(x)=-\log \sum_{i} \exp \left(f_{i}(x)\right)
$$

where $E(x)$ represents the energy of input $x, f_{i}(x)$ are the logits (pre-softmax activations) produced by the model for class $i$. This function calculates the energy level of an input sample, with lower energy indicating a higher likelihood of the sample being in-distribution (known) and higher energy suggesting it is an OOD (unknown) sample. This method effectively utilizes the model's predictive uncertainty to identify potential OOD samples, enhancing the system's ability to distinguish between known and unknown inputs.

\section*{3. Methodology}

In this section, we discuss VarMax in §3.1, a method for confidence scoring in OSR that calculates the logits and their variance in the last layer of a deep neural network. We describe establishing thresholds to accurately separate known from unknown data points in §3.2, focusing on optimizing sensitivity and specificity.

Figure 2 illustrates an architecture developed to address the biases found in traditional closed-set recognition algorithms like softmax and integration of our contribution, VarMax algorithm.

In a standard DNN, the architecture utilizes softmax function in its final layer to predict probabilities of each output class. Instead, we propose VarMax algorithm, which computes the variance of the logits created right before the last layer of the DNN. A high variance indicates a high confidence that the data point is from a known class. However, a low variance means the data point is new or unknown to the model. In §4.3, we show this hypothesis to be correct empirically.

\subsection*{3.1. VarMax: Confidence Score for Enhancing OSR}

The VarMax algorithm (see Algorithm 1) is an approach that extends the predictive power of neural network classifiers by performing a post hoc analysis of their outputs. It is designed to quantify the predictions' confidence level by examining the variance of logits dispersion, which are the direct outputs of a neural network's final layer before any normalization, like the softmax function, is applied.

We initiated our investigation by examining the variations in the logit data from the final layer of the

\begin{figure}
\includegraphics[alt={},max width=\textwidth]{https://cdn.mathpix.com/cropped/82a9a401-c001-46bd-9883-ce8261a5df26-04.jpg?height=304&width=790&top_left_y=214&top_left_x=1095}
\captionsetup{labelformat=empty}
\caption{Figure 2: VarMax execution}
\end{figure}
neural network, aiming to discern the differing patterns between known and unknown logit data. Initially, we fed the model input data from known classes exposed during training, recording the logits and analyzing their variance. This process was repeated for data not shown at training, i.e., unknown classes. Our observations reveal that the variance associated with known logits surpasses that of unknown logits. For empirical confirmation of this hypothesis, please see 4.3.
```
Algorithm 1 VarMax Algorithm
Require: $X_{i}$, the input for which to predict logits.
Ensure: A determination of whether $X_{i}$ is a known or
    unknown sample.
    Calculate Logits:
    for each class $y_{j}$ do
        Obtain the predicted logits $L_{i}^{j}$ for $X_{i}$.
    end for
    Calculate Variance of Logits (VarMax):
    Calculate the variance of the absolute values of
    logits:
    Variance $=\frac{1}{n} \sum_{j=1}^{s}\left|L_{i}^{j}-\operatorname{mean}\left(\left|L_{i}^{j}\right|\right)\right|$
    Set a Threshold:
    Define a threshold for the variance based on your
    data and problem.
    Detect Unknowns:
    if variance is below the threshold then
        Classify the input $X_{i}$ as an unknown sample.
    else
        Classify the input $X_{i}$ as a known sample.
    end if
```


Mathematically, suppose an input vector $X_{i}$, a neural network classifier computes a corresponding logit vector $L_{i}=\left\{l_{1}, l_{2}, \ldots, l_{N}\right\}$ for each class $y_{j}$. These logits represent the unnormalized $\log$ probabilities that the input belongs to each class. The VarMax algorithm processes these logits to extract a measure of confidence. It computes the variance of the logits' absolute values according to the formula:

$$
\operatorname{Variance}\left(L_{i}\right)=\frac{1}{N} \sum_{j=1}^{N}\left|l_{j}-\operatorname{mean}\left(\left|L_{i}\right|\right)\right|^{2}
$$

where $N$ is the number of classes. The rationale behind using absolute values is to assess the dispersion in a scale-invariant manner, emphasizing deviations from the mean prediction level.

A higher variance signifies a logit distribution with more spread, indicating that the classifier's predictions are more confident and possibly more accurate, given that the model has been exposed to similar samples during training. Conversely, a lower variance might suggest that the classifier is uncertain about its predictions, reflecting either a lack of familiarity with the input or a genuinely ambiguous input. For empirical confirmation of this hypothesis, please see §4.4.

\subsection*{3.2. Setting the Threshold}

Determining an appropriate threshold for variance is a critical component of the VarMax algorithm. This threshold $\theta$ is not universally fixed but is calibrated based on the distribution of variance scores observed on a validation set representative of known samples. It is chosen to optimize the trade-off between sensitivity and specificity when classifying inputs as known or unknown:
if Variance $\left(L_{i}\right)<\theta$, then classify $X_{i}$ as ambiguous; else classify $X_{i}$ as known.
Inputs that yield a variance score below $\theta$ are labeled as unknown, indicating a prediction with lower confidence. This may suggest that the classifier needs to be sufficiently trained on similar data. In contrast, inputs with a variance score exceeding $\theta$ are considered known, implying that the classifier's predictions are made with higher confidence and are more likely to be accurate.

For identifying the biasness of each algorithm, it is important to have an impartial threshold selection measure. In this case we used a rudimentary Receiver Operating Characteristic (ROC) selection from the binary classification between closed set sample and open set sample. Specifically, we selected a point corresponding to $80 \%$ of the softmax recall for the data. We do this because the softmax recall is directly tied to the model training fit, therefore, the point at $80 \%$ will eventually be reached by all algorithms, while not favoring any mechanism over the other.

\section*{4. Experimentation}

In this section, we detail the experimental setup in §4.1 and the datasets used in §4.2.

We, then, present our experiments (i) Testing our hypothesis that logits belonging to known samples show higher variance than those of unknown samples in §4.3, and (ii) Biasness study and performance comparison on Known vs. Unknown identification in §4.4.

Please note that this paper does not aim to present significantly high F 1 -scores for the algorithms by applying hyperparameter tuning and finding the maximum performance for each algorithm. We aim to show the capability of end-layers with basic architectures and identify their advantages and biases. Therefore, F-1 scores shown are not tuned and they are not the highest scores that can be acquired with any of these algorithms. However, the simple network setup is impartial, so we can assess the end-layers against each other.

\subsection*{4.1. Experimental Setup}

We employ a compact fully connected CNN featuring three layers utilizing ReLU for feature extraction and max-pooling for dimensionality reduction. Post-processing, the data is transformed into high-level features, which are then analyzed by two fully connected layers to discern complex patterns for classification before being output into logits associated with each class by using a third fully connected layer. Our model operates with a batch size of 32, a learning rate of 0.001 , and employs the SGD optimizer. The model was executed on 10 epochs.

The CICIDS dataset was run with a different structure due to being more complex and being the focus of related work. The primary differences are that Leaky Relu was used instead of Relu, dropout was used for each fully connected layer, one more fully connected layer was used, the batch size was 1000 for 100 epochs, and the Adam optimizer was used. The tests were also run on a more powerful computer containing NVIDIA RTX A6000 graphics cards with CUDA version 11.8, utilizing 30 GB of RAM.

\subsection*{4.2. Datasets}

To test VarMax, we have performed our experiments on six datasets, three of them being image datasets, and three of them have samples represented as vectors $n \times$ 1. For model structure, we used 1d convolution for the vector datasets and 2d convolution for the image datasets to maintain a more consistent model structure.
MNIST. (LeCun et al., 1998) The MNIST database of handwritten digits is a simple image dataset containing 60,000 training and 10, 000 testing images. Each image is a single handwritten digit, 0-9, that is centered in a black and white image. In our tests the digits 7, 8, and 9 were classified as the unknowns - this dataset's purpose was to test simple image datasets.
FashionMNIST. (Xiao et al., 2017) This dataset is a more challenging image dataset with similar structure to MNIST. The digits in MNIST are replaced with

\begin{figure}
\includegraphics[alt={},max width=\textwidth]{https://cdn.mathpix.com/cropped/82a9a401-c001-46bd-9883-ce8261a5df26-06.jpg?height=944&width=1555&top_left_y=210&top_left_x=259}
\captionsetup{labelformat=empty}
\caption{Figure 3: Distribution of Logits for Known and Unknown Data in all datasets}
\end{figure}

10 categories of fashion items. In our tests, trousers, pullovers, and dresses were classified as the unknowns. This dataset's purpose was to test lightly complex image datasets.

Food101. (Bossard et al., 2014) Food101 is an image database containing 101 different types of food. Each item has 1000 pictures and $75 \%$ are used for training. In our tests, Baby Back Ribs, Beef Carpaccio, and Beef Tartare were classified as the unknowns. This dataset's purpose was to see reactions to complex datasets. To fit the dataset into the same format, for our tests, each image was transformed into a $200 \times 200$ grayscale image.

Covertype. (Blackard, 1998) This dataset is a 54-feature multivariate dataset with 7 target classes. These variations include elevation, slope, distance to water features, and 40 binary columns for the presence or absence of soil types. In our tests, Ponderosa Pine, Cottonwood/Willow, and Aspen were classified as unknowns. This dataset is to identify the difference between image and numerical-based data.

CICIDS. (Sharafaldin et al., 2018) This dataset is a packet capture network data dataset that takes each packet sent during network attacks as an individual item. Each item has 1500 byte features, $0-255$, time to live, total length, protocol, time in transit, and packet target label. We use PayloadByte (Farrukh et al., 2022) to extract the data with payloads in creating vectors.

\begin{table}
\begin{tabular}{rrr}
\hline Dataset & \begin{tabular}{r} 
Average known \\
logit variance
\end{tabular} & \begin{tabular}{r} 
Average unknown \\
logit variance
\end{tabular} \\
\hline MNIST & 43.53 & 12.49 \\
\hline FashionMNIST & 25.72 & 3.45 \\
\hline Food101 & 3.35 & 3.22 \\
\hline Covertype & 17.54 & 3.12 \\
\hline CICIDS2017 & $122,241.60$ & $27,777.90$ \\
\hline
\end{tabular}
\captionsetup{labelformat=empty}
\caption{Table 1: Table of average variances, absolute value not applied}
\end{table}

\subsection*{4.3. Analyzing Logit Distributions Across Known and Unknown Datasets}

We conducted experiments using all six datasets to understand the variances of DNN logits concerning known and unknown datasets. For all datasets, the distribution of logits is depicted in Figure 3, in which the values of logits by indexes. As can be seen, the variance of unknown samples show lower variance across the board, while this is more obvious in vector sample datasets compared to image datasets. This phenomenon occurs because, through backpropagation (Werbos, 1990), the neural network fine-tunes its parameters to favor the selection of the class most likely to match the predicted class. Conversely, for unknown logit variance, we observe diminished variance attributed to the neural network's absence of a targeted class selection, given its

\begin{figure}
\includegraphics[alt={},max width=\textwidth]{https://cdn.mathpix.com/cropped/82a9a401-c001-46bd-9883-ce8261a5df26-07.jpg?height=1241&width=1466&top_left_y=214&top_left_x=298}
\captionsetup{labelformat=empty}
\caption{Figure 4: Biasness evalution with True Positive rate-based threshold selection}
\end{figure}
unfamiliarity with the class in question.
The image datasets in this paper, except MNIST, appear to have noticeably increased variance in the unknown logits which could contribute to a less accurate VarMax classifier. It is possible that lower variance is caused by the dimensionality of the convolution as that is one of the few changes between the datasets where 1d data uses 1d convolution while 2d data uses 2 d convolution.

\subsection*{4.4. Biasness Study}

Our study, as shown in Figure 4, evaluated the biases of various algorithms towards known and unknown datasets by assessing their performance through average F1-scores over a series of three controlled tests. Each test was done on a model kept in as similar structure as possible, with the threshold selection picked by getting an arbitrary value for the dataset, specifically aiming for a known class recall of $80 \%$ of the softmax recall on the first of the three tests per dataset. The results of
these tests were split into three categories for analysis, Knowns only, Unknowns only, and Total F1. Knowns only represents closed-set classification, for which, the F1-score is calculated with the classes the model was trained on. Unknowns only represents the open-set classification, and it consists solely of the data that was not included in any training, which were specified in the dataset section. Due to the size and complexity of the data in CICIDS2017 dataset, the experiments ran with 100 different tests while the model was being varied.

In Figure 4, it can be seen that SoftMax meets or exceeds both varMax and Energy end-layers' performance in Knowns only tests represented with the blue bar on all datasets. This is expected since SoftMax is the default end-layer for closed-set classification. However, open-set classification end-layers, varMax, and Energy perform comparably, with their performance varying across datasets. While it is expected for open-set classification end-layers to not perform as well as SoftMax in testing known samples, it is desirable for
them to come closer to the performance of SoftMax, exhibiting less bias towards knowns or unknowns.

Unknowns only tests represented with the red bar on all datasets in Figure 4. When we introduce unknown samples in testing, SoftMax cannot determine if they are unknown by the model, which means absolute bias toward electing if a sample is known in all cases. VarMax and Energy algorithms can identify if a test sample is unknown by the model. VarMax either performs comparably well or significantly exceeds the performance of the Energy algorithm across all datasets, or even if it performs worse, it still performs better in identifying knowns, which keeps the F1-score higher than Energy.

From the results seen in the figures, we infer that VarMax is less conservative than Energy when identifying unknowns unless the model is well trained, as seen in the MNIST results in Figure 4a. In addition to that, VarMax seems to perform better on Vector based data instead of image-based data. This might appear strange given the disparity between the knowns only and unknowns only in Figure 4d. However, the Softmax bars indicate a much higher rate of unknown data in the test set than the rest of the tests. Therefore, VarMax being less conservative is an advantage.

\section*{5. Discussion and Hybrid Approaches}

Our results demonstrate that while SoftMax performs optimally for known samples in closed-set classification, it fails to effectively handle unknown samples, exhibiting a strong bias toward classifying all samples as known. In contrast, varMax and Energy end-layers, designed for open-set classification, show a more balanced performance. VarMax, in particular, outperforms Energy in most scenarios, indicating its potential as a superior choice for handling unknowns. Interestingly, VarMax's performance varies between vector-based and image-based data, suggesting that its effectiveness may be data-type dependent. VarMax also provides slightly less computational complexity in getting the score for out-of-distribution detection.

A possible solution to increase known detection capability in open-set end-layers is the Top-Difference Classification Algorithm, which is designed for multi-class classification problems (Berenbeim et al., 2023). It operates on the principle of differentiating between the highest probabilities predicted for each class to decide whether the input is known or ambiguous. Combining SoftMax and VarMax can be useful in certain scenarios, especially in the cases where the researchers and practitioners would like to conservatively use VarMax to maintain the traditionality and confidence placed in the SoftMax algorithm for
known inputs.
Given an input vector $x \in \mathbb{R}^{\text {Input }}$ and a set of model parameters $\omega$, the algorithm performs the following steps:
1. Raw Score Calculation: The algorithm first computes a raw score vector $y=f(\omega, x) \in \mathbb{R}^{N}$ using the learning machine $f$.
2. SoftMax Normalization: The raw score vector $y$ is then normalized using the SoftMax function $\sigma$, resulting in a probability vector $p=\sigma(y) \in \mathbb{R}^{N}$.
3. Top Two Probabilities: From the probability vector $p$, the algorithm identifies the two highest probabilities, denoted as $p_{(1)}$ and $p_{(2)}$.
4. Probability Difference Calculation: The difference between these two probabilities is calculated as $\Delta p=\left|p_{(1)}-p_{(2)}\right|$.
5. Classification Decision: The algorithm then compares $\Delta p$ to a predefined threshold $\tau$. If $\Delta p> \tau$, the input $x$ is classified as known. Otherwise, it is classified as ambiguous.

The SoftMax function $\sigma$ is defined as:

$$
\sigma\left(y_{i}\right)=\frac{e^{y_{i}}}{\sum_{j=1}^{N} e^{y_{j}}}
$$

for each component $y_{i}$ of the vector $y$.
The decision criterion is based on the calculated difference $\Delta p$ and the threshold $\tau$. Formally, the decision rule is:

$$
\text { Decision }= \begin{cases}\text { known - use SoftMax } & \text { if } \Delta p>\tau \\ \text { ambiguous- use VarMax } & \text { otherwise }\end{cases}
$$


When we introduce this structure to VarMax algorithm as described to create an hybrid approach, we are able to use the SoftMax end-layer when the probability of a class is significantly high, and resort to varMax when the top probabilities are close. In this paper, our goal was to test the hypothesis behind VarMax, but hybrid approach gives significantly better results as seen on Figure 5, when tested on our most complex dataset, CICIDS2017.

\section*{6. Conclusions and Future Work}

This paper presents an approach to model network classification for open set recognition in deep neural networks, VarMax. This new approach leverages variance in neural network outputs to differentiate

\begin{figure}
\includegraphics[alt={},max width=\textwidth]{https://cdn.mathpix.com/cropped/82a9a401-c001-46bd-9883-ce8261a5df26-09.jpg?height=547&width=560&top_left_y=223&top_left_x=360}
\captionsetup{labelformat=empty}
\caption{Figure 5: VarMax with Top-Difference algorithm}
\end{figure}
between familiar and novel inputs using variance-based categorization of ambiguous samples. Our broad tests on benchmark datasets show that VarMax performs in a considerable manner when given one dimensional based data or well trained models. This consideration does well in balancing both known and unknown classes given time for adjustment.

However, the variability in the results underscores the need for further investigation into the factors influencing end-layer performance in different data contexts. The incapability of detecting unknowns by SoftMax highlights the limitations of traditional closed-set approaches and the necessity for more robust open-set methods like varMax and Energy. Overall, our findings emphasize the importance of selecting appropriate end-layers based on the specific characteristics and requirements of the dataset.

\section*{Acknowledgment}

This work was supported in part by the United States Military Academy (USMA) under Cooperative Agreement No. W911NF-22-2-0160. The views and conclusions expressed in this paper are those of the authors and do not reflect the official policy or position of USMA, the United States Army, United States Department of Defense, or United States Government.

\section*{References}

Ahmad, Z., Shahid Khan, A., Wai Shiang, C., Abdullah, J., \& Ahmad, F. (2021). Network intrusion detection system: A systematic study of machine learning and deep learning approaches. Transactions on Emerging Telecommunications Technologies, 32(1), e4150.

AUEB, T. R., et al. (2016). One-vs-each approximation to softmax for scalable estimation of probabilities. Advances in Neural Information Processing Systems, 29.
Baye, G., Hussain, F., Oracevic, A., Hussain, R., \& Kazmi, S. A. (2021). Api security in large enterprises: Leveraging machine learning for anomaly detection. 2021 International Symposium on Networks, Computers and Communications (ISNCC), 1-6.
Baye, G., Silva, P., Broggi, A., Fiondella, L., Bastian, N. D., \& Kul, G. (2023). Performance analysis of deep-learning based open set recognition algorithms for network intrusion detection systems. NOMS 2023-2023 IEEE/IFIP Network Operations and Management Symposium, 1-6.
Berenbeim, A., Bierbrauer, D., Cruickshank, I., Thomson, R., \& Bastian, N. (2023). Applications of certainty scoring for machine learning classification in multi-modal contexts. Authorea Preprints.
Blackard, J. (1998). Covertype [DOI: https://doi.org/10.24432/C50K5N].
Bossard, L., Guillaumin, M., \& Van Gool, L. (2014). Food-101 - mining discriminative components with random forests. European Conference on Computer Vision.
Elmasry, W., Akbulut, A., \& Zaim, A. H. (2019). Empirical study on multiclass classification-based network intrusion detection. Computational Intelligence, 35(4), 919-954.
Farrukh, Y. A., Khan, I., Wali, S., Bierbrauer, D., Pavlik, J. A., \& Bastian, N. D. (2022). Payload-Byte: A Tool for Extracting and Labeling Packet Capture Files of Modern Network Intrusion Detection Datasets. IEEE/ACM International Conference on Big Data Computing, Applications and Technologies (BDCAT2022).
Farrukh, Y. A., Wali, S., Khan, I., \& Bastian, N. D. (2023). Detecting unknown attacks in iot environments: An open set classifier for enhanced network intrusion detection. MILCOM 2023-2023 IEEE Military Communications Conference (MILCOM), 121-126.
Grathwohl, W., Wang, K.-C., Jacobsen, J.-H., Duvenaud, D., Norouzi, M., \& Swersky, K. (2019). Your classifier is secretly an energy based model and you should treat it like one. arXiv preprint arXiv:1912.03263.

Guo, C., Pleiss, G., Sun, Y., \& Weinberger, K. Q. (2017). On calibration of modern neural networks. International conference on machine learning, 1321-1330.
Hassen, M., \& Chan, P. K. (2020). Learning a neural-network-based representation for open set recognition. Proceedings of the 2020 SIAM International Conference on Data Mining, 154-162.
Hsu, Y.-C., Shen, Y., Jin, H., \& Kira, Z. (2020). Generalized odin: Detecting out-of-distribution image without learning from out-of-distribution data. IEEE/CVF Conference on Computer Vision and Pattern Recognition, 10951-10960.
Khosla, S., \& Gangadharaiah, R. (2022). Evaluating the practical utility of confidence-score based techniques for unsupervised open-world classification. 3rd Workshop on Insights from Negative Results in NLP, 18-23.
Larson, M. G. (2008). Analysis of variance. Circulation, 117(1), 115-121.
LeCun, Y., Bottou, L., Bengio, Y., \& Haffner, P. (1998). Gradient-based learning applied to document recognition. Proceedings of the IEEE, 86(11), 2278-2324.
LeCun, Y., Chopra, S., Hadsell, R., Ranzato, M., \& Huang, F. (2006). A tutorial on energy-based learning. Predicting structured data, 1(0).
Liang, S., Li, Y., \& Srikant, R. (2017). Enhancing the reliability of out-of-distribution image detection in neural networks. arXiv preprint arXiv:1706.02690.
Liu, W., Wang, X., Owens, J., \& Li, Y. (2020). Energy-based out-of-distribution detection. Advances in Neural Information Processing Systems.
Mandelbaum, A., \& Weinshall, D. (2017). Distance-based confidence score for neural network classifiers. arXiv preprint arXiv:1709.09844.
Matejek, B., Gehani, A., Bastian, N. D., Clouse, D., Kline, B., \& Jha, S. (2024). Safeguarding network intrusion detection models from zero-day attacks and concept drift. the 6th International Conference on Artificial Intelligence and Computer Science (AICS 2024).

Padhy, S., Nado, Z., Ren, J., Liu, J., Snoek, J., \& Lakshminarayanan, B. (2020). Revisiting one-vs-all classifiers for predictive uncertainty and out-of-distribution detection in neural networks. arXiv preprint arXiv:2007.05134.

Scheirer, W. J., de Rezende Rocha, A., Sapkota, A., \& Boult, T. E. (2012). Toward open set recognition. IEEE transactions on pattern analysis and machine intelligence, 35(7), 1757-1772.
Shafiq, M., \& Gu, Z. (2022). Deep residual learning for image recognition: A survey. Applied Sciences, 12(18), 8972.
Sharafaldin, I., Lashkari, A. H., \& Ghorbani, A. A. (2018). Intrusion detection evaluation dataset (cic-ids2017). Proceedings of the of Canadian Institute for Cybersecurity.
Shu, L., Xu, H., \& Liu, B. (2017). Doc: Deep open classification of text documents. arXiv preprint arXiv:1709.08716.
Szegedy, C., Vanhoucke, V., Ioffe, S., Shlens, J., \& Wojna, Z. (2016). Rethinking the inception architecture for computer vision. IEEE conference on computer vision and pattern recognition, 2818-2826.
Thulasidasan, S., Chennupati, G., Bilmes, J. A., Bhattacharya, T., \& Michalak, S. (2019). On mixup training: Improved calibration and predictive uncertainty for deep neural networks. Advances in Neural Information Processing Systems, 32.
Tunnell, M., Chung, H., \& Chang, Y. (2022). A novel convolutional neural network for emotion recognition using neurophysiological signals. 2022 International Conference on Robotics and Automation (ICRA), 792-797. https://doi. org/10.1109/ICRA46639.2022.9811868
Wang, Y., Li, B., Che, T., Zhou, K., Liu, Z., \& Li, D. (2021). Energy-based open-world uncertainty modeling for confidence calibration. IEEE/CVF International Conference on Computer Vision, 9302-9311.
Werbos, P. J. (1990). Backpropagation through time: What it does and how to do it. Proceedings of the IEEE, 78(10), 1550-1560.
Wong, J. A., Berenbeim, A. M., Bierbrauer, D. A., \& Bastian, N. D. (2023). Uncertainty-quantified, robust deep learning for network intrusion detection. 2023 Winter Simulation Conference (WSC), 2470-2481.
Xiao, H., Rasul, K., \& Vollgraf, R. (2017, August 28). Fashion-mnist: A novel image dataset for benchmarking machine learning algorithms. arXiv: cs.LG/1708.07747 [cs.LG].
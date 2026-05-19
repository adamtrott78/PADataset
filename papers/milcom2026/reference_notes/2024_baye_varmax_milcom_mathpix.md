\title{
varMax: Towards Confidence-Based Zero-Day Attack Recognition
}

\author{
Gaspard Baye \\ Computer and Information Science \\ University of Massachusetts Dartmouth \\ Dartmouth, USA \\ bgaspard@umassd.edu
}

\author{
Priscila Silva \\ Electrical and Computer Engineering \\ University of Massachusetts Dartmouth \\ Dartmouth, MA, USA \\ psilva4@umassd.edu
}

\author{
Alexandre Broggi \\ Computer and Information Science \\ University of Massachusetts Dartmouth \\ Dartmouth, MA, USA \\ abroggi@umassd.edu
}

\author{
Nathaniel D. Bastian \\ Army Cyber Institute \\ United States Military Academy \\ West Point, NY, USA \\ nathaniel.bastian@westpoint.edu
}

\author{
Lance Fiondella \\ Electrical and Computer Engineering \\ University of Massachusetts Dartmouth \\ Dartmouth, MA, USA \\ lfiondella@umassd.edu
}

\author{
Gokhan Kul \\ Computer and Information Science \\ University of Massachusetts Dartmouth \\ Dartmouth, MA, USA \\ gkul@umassd.edu
}

\begin{abstract}
Detecting zero-day attacks, which exploit unknown vulnerabilities, is vital in mission-critical systems. Deep Neural Networks (DNNs) often fails to identify unknown activity, as they make overly confident predictions due to SoftMax function, effective at identifying known attacks but is not structured to identify unknown activity patterns. Open-Set recognition (OSR) algorithms designed for DNNs tend to flag inputs as unknown, needing a balanced approach. To address this, we introduce varMax, a bias-neutral OSR technique using DNN logit variance to distinguish known from unknown inputs. It has three components: (1) a top-difference algorithm comparing top two softmax scores to a threshold, (2) a method classifying ambiguous samples based on logit variance, and (3) an energy-based out-ofdistribution function enhancing classification accuracy and trustworthiness. Our evaluation shows varMax outperforms leading methods in identifying unknown activities and improves DNN confidence and robustness in distinguishing between known and unknown inputs. This research marks a significant step forward in the development of reliable and unbiased intrusion detection systems for cybersecurity threats.
\end{abstract}

Index Terms-Network intrusion detection, deep neural networks, open-set recognition, zero-day attacks

\section*{I. Introduction}

Deep neural networks (DNNs) have achieved notable success in anomaly [1], malware [2], and network intrusion detection [3] tasks, demonstrating high accuracy and F-1 scores in various data classes. This highlights their potential in cybersecurity applications, including Network Intrusion Detection Systems (NIDS). However, DNNs face a fundamental limitation due to their closed-set nature [4], making them less effective against zero-day attacks and novel threats [5]. The softmax function is designed for closed-set predictions, which leads to overconfident classifications of unseen data as known categories, resulting in false predictions [6].

Several open-set recognition (OSR) algorithms [7], [8] have been developed to address this by replacing softmax to identify if a sample belongs to a known class. However, these algorithms were initially designed for images [6], [9]. Our previous
work [10] found that while OSR algorithms can distinguish known from unknown inputs in network intrusion detection, they often bias towards classifying inputs as unknown, reducing their effectiveness. This underscores the need for a balanced approach to accurately calibrate confidence levels for both known and unknown data classes, ensuring zero-day attacks are neither overlooked nor excessively flagged.

This paper proposes a novel methodology to address the limitations of traditional softmax-based DNNs and OSR algorithms. Our approach uses a bias-neutral strategy to identify unknown samples, which could be either benign activities or zero-day attacks, enhancing DNN's ability to recognize and classify unseen attack patterns, thereby improving resilience against emerging threats. Analytical evaluations show our methodology addresses biases in existing intrusion detection methods and sets a new reliability benchmark for integrating DNNs into NIDS applications. We initially calculate the softmax probabilities $P[11]$ for the input classes, focusing on the difference $\Delta$ between the top-ranked $P_{1}$ and second-ranked $P_{2}$ probabilities. A small $\Delta$ indicates classification uncertainty [12]. To address this, we introduce varMax, a technique evaluating the variance $\sigma^{2}$ [13] in DNN logits, producing a variance confidence score. Known inputs show higher variance $\sigma_{\text {high }}^{2}$, while unknown inputs show lower variance $\sigma_{\text {low }}^{2}$. We also adopt an energy-based out-of-distribution (OOD) algorithm [7], previously identified as effective in handling unknown network packets [10]. Combining probability assessment with variance analysis ensures a more accurate and reliable input classification system.

Concretely, the contributions of this paper are: (i) Enhancing softmax capabilities from a closed-set to an open-set framework by addressing classification uncertainties through the top two differences, calculating the difference between the top two softmax probabilities to determine prediction certainty. (ii) Introducing varMax to evaluate variances in DNN logits, developing a variance confidence score that differ-
entiates known (high variance) from unknown (low variance) inputs. (iii) Integrating an energy-based OOD algorithm to enhance the precision of identifying unknown inputs, effectively handling ambiguous classifications. Our comprehensive experiments using benchmark datasets demonstrate that our approach significantly improves the detection of unknown or zero-day attacks in network intrusion detection.

\section*{II. Preliminaries}

This section reviews the principles of OSR and the nature of zero-day attacks.

\section*{A. Open-Set Recognition}

OSR addresses the challenge where novel classes, which were not present during the training phase, emerge during testing and in the wild [14]. This necessitates that classifiers be adept not only at recognizing established classes but also at managing classes that are newly encountered, such as zeroday threats in the realm of network security. Consequently, it is essential for these classifiers to incorporate a rejection mechanism for instances that belong to these unknown, zeroday categories. Figure 1 visualizes the process executed by an open-set classifier, which includes the identification of unknown classes while simultaneously classifying known ones.

\begin{figure}
\includegraphics[alt={},max width=\textwidth]{https://cdn.mathpix.com/cropped/4bd2d0d3-c574-4bf9-a46e-74aacff6dc14-2.jpg?height=302&width=770&top_left_y=1213&top_left_x=223}
\captionsetup{labelformat=empty}
\caption{Fig. 1: OSR acknowledges that knowledge available at training is incomplete, therefore, when it encounters unknown classes during testing and inference, it needs to identify what it is not trained on, and forward to expert mechanisms that may have the capability of labeling it}
\end{figure}

\section*{B. Zero-Day Attacks}

A zero-day attack involves exploiting a previously undisclosed vulnerability in software. This type of cyberattack is particularly challenging to defend against because until the vulnerability is made public, there's no way to patch the software or antivirus programs to detect the attack using traditional signature-based methods [5].

DNN models for cybersecurity are typically trained on known data. However, zero-day attacks, which are not identified until they are publicly exposed, lack pre-existing datasets. As a result, DNN-based network security systems often fail to identify these attacks. This misclassification can lead to significant consequences for the targeted systems or organizations, as the novel or unknown nature of zero-day attacks bypasses the predictive capabilities of the existing defensive DNN mechanisms. For instance, the vulnerability timeline depicted in Figure 2 starts with a vulnerability emerging in a popular software product due to an exploitable programming

\begin{figure}
\includegraphics[alt={},max width=\textwidth]{https://cdn.mathpix.com/cropped/4bd2d0d3-c574-4bf9-a46e-74aacff6dc14-2.jpg?height=435&width=880&top_left_y=197&top_left_x=1082}
\captionsetup{labelformat=empty}
\caption{Fig. 2: Zero-Day Attack Timeline. In zero-day attacks, events do not always adhere to this sequence. Typically, the timeline is characterized by $t_{d}>t_{p} \geq t_{i}>t_{v}$ and $t_{0} \geq t_{i}$. Determining a consistent relationship between $t_{i}$ and $t_{e}$ is usually challenging. Notably, in zero-day attacks, itś often the case that $t_{0}>t_{e}$.}
\end{figure}
error ( $t_{v}$ ). Attackers discover this vulnerability and exploit it stealthily ( $t_{e}$ ). Later, the software vendor detects the vulnerability ( $t_{i}$ ) and makes it public ( $t_{0}$ ), which triggers the release of countermeasures like antivirus signatures ( $t_{s}$ ) and patches ( $t_{p}$ ). The threat posed by the vulnerability subsides once the patch is fully deployed ( $t_{d}$ ). These disclosure events ( $t_{0}$ ) are documented in databases like Common Vulnerability Exposures. A zero-day attack is marked by exploiting a vulnerability before its public disclosure ( $t_{0}>t_{e}$ ).

\section*{III. Methodology}

This section introduces the top-two difference algorithm in §III-A, which assesses the disparity in softmax probability scores. We then present varMax §III-B, a method for confidence scoring in open-set recognition that calculates the logits and their variance in the second to last layer of a deep neural network. Subsequent sections describe a method for establishing thresholds (§III-C) to accurately separate known from unknown data points, focusing on optimizing sensitivity.

Figure 3 illustrates an architecture developed to address the biases found in traditional closed-set recognition algorithms like softmax and integration of our contribution, varMax algorithm with OSR algorithms. When network packets are fed into a standard DNN, it uses a softmax function as the end layer to predict probabilities of output classes. Next, the toptwo difference algorithm (see §III-A) evaluates the difference between the highest two softmax probability scores. If the difference exceeds a specific threshold, we can confidently classify it under a known class. If not, and we turn to the VarMax algorithm (detailed in §III-B Alg. 1), which computes the variance of the logits created right before the last layer of the DNN. As outlined in §III-C, a high variance indicates a high confidence that the data point is from a known class. However, a low variance means the data point is novel to the model. To verify the unknown classification confidence, we use an energy-based OOD method to validate our hypothesis.

\section*{A. Top-Difference Classification Algorithm}

The Top-Difference Classification Algorithm is designed for multi-class classification problems [12]. It operates on the principle of differentiating between the highest probabilities predicted for each class to decide whether the input is known or ambiguous.

Given an input vector $x \in \mathbb{R}^{\text {Input }}$ and a set of model parameters $\omega$, the algorithm performs the following steps:
1) Raw Score Calculation: The algorithm first computes a raw score vector $y=f(\omega, x) \in \mathbb{R}^{N}$ using the learning machine $f$.
2) SoftMax Normalization: The raw score vector $y$ is then normalized using the SoftMax function $\sigma$, resulting in a probability vector $p=\sigma(y) \in \mathbb{R}^{N}$.
3) Top Two Probabilities: From the probability vector $p$, the algorithm identifies the two highest probabilities, denoted as $p_{(1)}$ and $p_{(2)}$.
4) Probability Difference Calculation: The difference between these two probabilities is calculated as $\Delta p= \left|p_{(1)}-p_{(2)}\right|$.
5) Classification Decision: The algorithm then compares $\Delta p$ to a predefined threshold $\tau$. If $\Delta p>\tau$, the input $x$ is classified as known. Otherwise, it is classified as ambiguous.
The SoftMax function $\sigma$ is defined as:

$$
\sigma\left(y_{i}\right)=\frac{e^{y_{i}}}{\sum_{j=1}^{N} e^{y_{j}}}
$$

for each component $y_{i}$ of the vector $y$.
The decision criterion is based on the calculated difference $\Delta p$ and the threshold $\tau$. Formally, the decision rule is:

$$
\text { Decision }= \begin{cases}\text { known } & \text { if } \Delta p>\tau \\ \text { ambiguous } & \text { otherwise }\end{cases}
$$


\section*{B. VarMax: Confidence Score for Enhancing OSR}

The VarMax algorithm 1 is an approach that extends the predictive power of neural network classifiers by performing a post hoc analysis of their outputs. It is designed to quantify the predictions' confidence level by examining the variance of logits dispersion, which are the direct outputs of a neural network's final layer before any normalization, like the softmax function, is applied.
1) Computing Logits and Variance: We initiated our investigation by examining the variations in the logit data from the final layer of the neural network, aiming to discern the differing patterns between known and unknown logit data. Initially, we fed the model input data from known classes exposed during training, recording the logits and analyzing their variance. This process was repeated for data not shown at training, i.e., unknown classes. Our observations reveal that the variance associated with known logits surpasses that of unknown logits.

Mathematically, suppose an input vector $X_{i}$, a neural network classifier computes a corresponding logit vector $L_{i}=$

\begin{figure}
\includegraphics[alt={},max width=\textwidth]{https://cdn.mathpix.com/cropped/4bd2d0d3-c574-4bf9-a46e-74aacff6dc14-3.jpg?height=605&width=745&top_left_y=167&top_left_x=1142}
\captionsetup{labelformat=empty}
\caption{Fig. 3: Classification of network intrusion detection system traffic using Softmax and varMax as a confidence booster}
\end{figure}
$\left\{l_{1}, l_{2}, \ldots, l_{N}\right\}$ for each class $y_{j}$. These logits represent the unnormalized log probabilities that the input belongs to each class. The VarMax algorithm processes these logits to extract a measure of confidence. It computes the variance of the logits' absolute values according to the formula:

$$
\operatorname{Variance}\left(L_{i}\right)=\frac{1}{N} \sum_{j=1}^{N}\left|l_{j}-\operatorname{mean}\left(\left|L_{i}\right|\right)\right|^{2}
$$

where $N$ is the number of classes. The rationale behind using absolute values is to assess the dispersion in a scale-invariant manner, emphasizing deviations from the mean prediction level. A higher variance signifies a logit distribution with more spread, indicating that the classifier's predictions are more confident and possibly more accurate, given that the model has been exposed to similar samples during training. Conversely, a lower variance might suggest that the classifier is uncertain about its predictions, reflecting either a lack of familiarity with the input or a genuinely ambiguous input.

\section*{C. Setting the Threshold}

Determining an appropriate threshold for variance is a critical component of the VarMax algorithm. This threshold $\theta$ is not universally fixed but is calibrated based on the distribution of variance scores observed on a validation set representative of known samples. It is chosen to optimize the trade-off between sensitivity and specificity when classifying inputs as known or unknown:
if $\operatorname{Variance}\left(L_{i}\right)<\theta$, then classify $X_{i}$ as ambiguous; else classify $X_{i}$ as known.

Inputs that yield a variance score below $\theta$ are labeled as unknown, indicating a prediction with lower confidence. This may suggest that the classifier needs to be sufficiently trained on similar data. In contrast, inputs with a variance score exceeding $\theta$ are considered known, implying that the classifier's predictions are made with higher confidence and are more likely to be accurate.
```
Algorithm 1 VarMax Algorithm
Require: $X_{i}$, the input for which to predict logits.
Ensure: A determination of whether $X_{i}$ is a known or un-
    known sample.
    Calculate Logits:
    for each class $y_{j}$ do
        Obtain the predicted logits $L_{i}^{j}$ for $X_{i}$.
    end for
    Calculate Variance of Logits (VarMax):
    Calculate the variance of the absolute values of logits:
    Variance $=\frac{1}{n} \sum_{j=1}^{s}\left|L_{i}^{j}-\operatorname{mean}\left(\left|L_{i}^{j}\right|\right)\right|$
    Set a Threshold:
    Define a threshold for the variance based on your data and
    problem.
    Detect Unknowns:
    if variance is below the threshold then
        Classify the input $X_{i}$ as an unknown sample.
    else
        Classify the input $X_{i}$ as a known sample.
    end if
```


\section*{D. Energy-based OOD}

Finally, the output of our VarMax algorithm determines if the system should depend on the output by the default closedworld setting (i.e., SoftMax), or an open-world recognition algorithm (i.e., Energy-based OOD). In our case, we use the energy-based function based on our previous work [10], enhancing our ability to recognize unknowns effectively. Weitang et al. [7] introduced a method that employs energy scores for OOD sample detection, proving them superior to traditional Softmax scores in distinguishing between in-distribution and OOD samples. Energy scores, less prone to overconfidence than softmax, are more closely related to the probability density of inputs. The energy-based function for OOD detection, defined as:

$$
E(x)=-\log \sum_{i} \exp \left(f_{i}(x)\right)
$$

where $E(x)$ represents the energy of input $x, f_{i}(x)$ are the logits (pre-softmax activations) produced by the model for class $i$. This function calculates the energy level of an input sample, with lower energy indicating a higher likelihood of the sample being in-distribution (known) and higher energy suggesting it is an OOD (unknown) sample. This method effectively utilizes the model's predictive uncertainty to identify potential OOD samples, enhancing the system's ability to distinguish between known and unknown inputs.

\section*{IV. Experimentation}

In this section, we detail the experimental setup and how we assess the effectiveness of our suggested algorithms using benchmark datasets for NIDS.

We employ a compact fully connected CNN featuring three layers, utilizing Leaky ReLU for feature extraction, maxpooling for dimensionality reduction, and dropout to mitigate overfitting. Post-processing, the data is transformed into highlevel features, which are then analyzed by two fully connected
layers to discern complex patterns for classification. Our model operates with a batch size of 1000 , a learning rate of 0.01 , and employs the Adam optimizer. The model was executed on NVIDIA RTX A6000 graphics cards with CUDA version 11.8 , utilizing 30 GB of RAM throughout 100 epochs.

We employ widely used evaluation metrics such as the Area Under the Receiver Operating Characteristic (AUROC) curve [15] and the F1 - score [16] to evaluate our algorithm's capability in identifying known and unknown data samples. These measures assess the model's effectiveness in detecting and classifying data samples under specific classes. The $F 1-$ score is particularly vital in contexts of data imbalance, offering a balanced measure of the model's precision and recall. Together, these metrics facilitate a thorough evaluation, advancing algorithms for cybersecurity by differentiating between familiar and novel threats.

We use a popular benchmark dataset, including the CICIDS [17] and the UNSW [18]. These datasets are instrumental in this evaluation, featuring a diverse mix of benign and malicious network traffic across 15 CICIDS classes and 9 UNSW dataset classes. These datasets encapsulate the complexities of real-world network traffic, providing a robust testing ground for our algorithm. We simulate zero-day attack scenarios by training on a comprehensive mix of known class samples and testing against known but withheld unknown attack samples. This approach ensures our model is tested against novel threats it has not seen before, mirroring real-world conditions where new threats continuously emerge. In each test, at least 1000 samples for each class were used.

\section*{V. Results and Discussion}

This section illustrates the performance of our approach against existing leading OSR algorithms using popular benchmark datasets.
Analyzing Logit Distributions for Knowns and Unknowns. We conducted experiments using the CICIDS and UNSW datasets to understand the variances of DNN logits concerning known and unknown datasets. Figure 6 illustrate the logits distribution for known and unknown data within the CICIDS and UNSW datasets, respectively. For both datasets, the distribution of logits across a batch size of 100 samples is depicted. The distribution, as we tested beyond the samples shown in the graphs, confirms our hypothesis that, through backpropagation [19], the neural network fine-tunes its parameters to favor the selection of the class most likely to match the predicted class. Conversely, for unknown logit variance, we observe diminished variance attributed to the neural network's absence of a targeted class selection, given its unfamiliarity with the class in question.
Biasness Study. Our study, as shown in Figure 7, evaluated the biases of various algorithms towards known and unknown datasets by assessing their performance through average F1-scores over a series of 100 controlled tests. Each test featured an equal distribution of known and unknown classes, meticulously alternating the classification challenge

\begin{figure}
\includegraphics[alt={},max width=\textwidth]{https://cdn.mathpix.com/cropped/4bd2d0d3-c574-4bf9-a46e-74aacff6dc14-5.jpg?height=523&width=1817&top_left_y=163&top_left_x=156}
\captionsetup{labelformat=empty}
\caption{Fig. 4: Evaluating F1 - Scores via Confidence-Based Analysis of Different OSR Algorithms on the CICIDS Dataset}
\end{figure}

\begin{figure}
\includegraphics[alt={},max width=\textwidth]{https://cdn.mathpix.com/cropped/4bd2d0d3-c574-4bf9-a46e-74aacff6dc14-5.jpg?height=554&width=1817&top_left_y=751&top_left_x=156}
\captionsetup{labelformat=empty}
\caption{Fig. 5: Evaluating F1-Scores via Confidence-Based Analysis of Different OSR Algorithms on the UNSW Dataset}
\end{figure}

\begin{figure}
\includegraphics[alt={},max width=\textwidth]{https://cdn.mathpix.com/cropped/4bd2d0d3-c574-4bf9-a46e-74aacff6dc14-5.jpg?height=546&width=1535&top_left_y=1347&top_left_x=300}
\captionsetup{labelformat=empty}
\caption{Fig. 6: Distribution of Logits for Known and Unknown Data in the CICIDS and UNSW Datasets}
\end{figure}
under the same hyperparameters and a consistent, fully connected neural network architecture. The suite of algorithms COOL, DOC, Energy, Open, Softmax, iiMod, and VarMax underwent thorough analysis to uncover any predispositions in accurately identifying and categorizing both familiar and novel data types. Our findings pointed to a marked inclination of Softmax towards better recognition of known datasets, evidenced by notably higher average $F 1-$ scores, underscoring its proficiency with recognizable patterns but a decline in handling unseen categories. Conversely, COOL, DOC, Energy, iiMod, and Open demonstrated a remarkable capability to embrace unknown datasets, showcasing their flexibility
and resilience in evolving settings but they struggle when it comes to knowns. Notably, VarMax exhibited a neutral stance, maintaining consistent performance irrespective of the dataset familiarity, an attribute highly desirable in scenarios demanding fair consideration of all data variants. By visualizing these findings through average F1 score comparisons, we underscore the imperative of discerning algorithmic bias in OSR algorithms.

Confidence Analysis. Figures 4 and 5 show how F1-Scores vary with the number of unknown classes in CICIDS and UNSW datasets. VarMax consistently achieves around $74 \%$ (CICIDS) and $72 \%$ (UNSW) F1-Scores, even as unknown

\begin{figure}
\includegraphics[alt={},max width=\textwidth]{https://cdn.mathpix.com/cropped/4bd2d0d3-c574-4bf9-a46e-74aacff6dc14-6.jpg?height=518&width=665&top_left_y=174&top_left_x=277}
\captionsetup{labelformat=empty}
\caption{Fig. 7: Average F1-Scores by Algorithm and Dataset Type}
\end{figure}
classes increase. In contrast, Softmax starts strong with 76\% (CICIDS) and 70\% (UNSW) F1-Scores but drops significantly with more unknowns due to its closed-set nature. Meanwhile, algorithms like COOL, DOC, Energy, and iiMod improve with more unknowns, especially Energy, which hits 77\% F1-Score at 8 unknown classes.

Testing on explicitly known samples (Figure 4b) reveals Softmax's strength in known class detection with $74 \%$ F1Scores in both datasets. VarMax matches this performance, showing its capability in known detection. Other algorithms, designed for unknown detection, show lower F1-Scores, with Energy peaking at $39 \%$.

Analysis of explicitly unknown samples (Figures 4c and 5c) confirms Softmax's struggle with unknowns. VarMax, excels with $71 \%$ F1-Scores, comparable to specialized OSR algorithms. This illustrates the distinct biases: Softmax favors knowns, OSR algorithms favor unknowns, and VarMax remains effectively neutral, supporting the need for the biasness study we performed.

\section*{VI. Conclusions and Future Work}

This paper presents a new approach, varMax, for improving network security through confident identification of zero-day attacks. Varmax, a bias-neutral method, leverages variance in neural network outputs to differentiate between familiar and novel inputs, incorporating a top-difference algorithm, variance-based categorization of ambiguous samples, and an enhanced OOD detection function. Our comprehensive tests on benchmark datasets show that varMax outperforms existing methods in recognizing both known and unknown threats with higher confidence and robustness. Unlike traditional models, which favor known inputs, varMax maintains impartiality, significantly advancing reliable threat detection in cybersecurity.

To ensure the resilience of this technique against sophisticated cyber threats, we will undertake further testing, particularly focusing on its robustness against adversarial attacks. This will help fortify the method against attackers possessing advanced cybersecurity skills. Currently, our system identifies unknown inputs, including both benign novelties and zero-day attacks; in the next phase, we plan to incorporate a fine-tuned Large Language Model to assign labels and descriptions to unidentified inputs, labeling both benign novel and zero-day
attacks, hence further bolstering our system's defenses against new and evolving threats.

\section*{Acknowledgment}

This work was supported in part by the United States Military Academy (USMA) under Cooperative Agreement No. W911NF-22-2-0160. The views and conclusions expressed in this paper are those of the authors and do not reflect the official policy or position of USMA, U.S. Army, U.S. Department of Defense, or U.S. Government.

\section*{References}
[1] G. Baye, F. Hussain, A. Oracevic, R. Hussain, and S. A. Kazmi, "Api security in large enterprises: Leveraging machine learning for anomaly detection," in 2021 International Symposium on Networks, Computers and Communications (ISNCC). IEEE, 2021, pp. 1-6.
[2] J. Singh and J. Singh, "A survey on machine learning-based malware detection in executable files," Journal of Systems Architecture, vol. 112, p. 101861, 2021.
[3] Z. Ahmad, A. Shahid Khan, C. Wai Shiang, J. Abdullah, and F. Ahmad, "Network intrusion detection system: A systematic study of machine learning and deep learning approaches," Transactions on Emerging Telecommunications Technologies, vol. 32, no. 1, p. e4150, 2021.
[4] M. Shafiq and Z. Gu, "Deep residual learning for image recognition: A survey," Applied Sciences, vol. 12, no. 18, p. 8972, 2022.
[5] S. Ali, S. U. Rehman, A. Imran, G. Adeem, Z. Iqbal, and K.-I. Kim, "Comparative evaluation of ai-based techniques for zero-day attacks detection," Electronics, vol. 11, no. 23, p. 3934, 2022.
[6] Y. Wang, B. Li, T. Che, K. Zhou, Z. Liu, and D. Li, "Energy-based openworld uncertainty modeling for confidence calibration," in Proceedings of the IEEE/CVF International Conference on Computer Vision, 2021, pp. 9302-9311.
[7] W. Liu, X. Wang, J. Owens, and Y. Li, "Energy-based out-of-distribution detection," Advances in Neural Information Processing Systems, 2020.
[8] M. Hassen and P. K. Chan, "Learning a neural-network-based representation for open set recognition," in Proceedings of the 2020 SIAM International Conference on Data Mining. SIAM, 2020, pp. 154-162.
[9] S. Khosla and R. Gangadharaiah, "Evaluating the practical utility of confidence-score based techniques for unsupervised open-world classification," in Proceedings of the Third Workshop on Insights from Negative Results in NLP, 2022, pp. 18-23.
[10] G. Baye, P. Silva, A. Broggi, L. Fiondella, N. D. Bastian, and G. Kul, "Performance analysis of deep-learning based open set recognition algorithms for network intrusion detection systems," in NOMS 20232023 IEEE/IFIP Network Operations and Management Symposium. IEEE, 2023, pp. 1-6.
[11] T. R. AUEB et al., "One-vs-each approximation to softmax for scalable estimation of probabilities," Advances in Neural Information Processing Systems, vol. 29, 2016.
[12] A. Berenbeim, D. Bierbrauer, I. Cruickshank, R. Thomson, and N. Bastian, "Applications of certainty scoring for machine learning classification in multi-modal contexts," Authorea Preprints, 2023.
[13] M. G. Larson, "Analysis of variance," Circulation, vol. 117, no. 1, pp. 115-121, 2008.
[14] W. J. Scheirer, A. de Rezende Rocha, A. Sapkota, and T. E. Boult, "Toward open set recognition," IEEE transactions on pattern analysis and machine intelligence, vol. 35, no. 7, pp. 1757-1772, 2012.
[15] D. Chicco and G. Jurman, "The advantages of the matthews correlation coefficient (mcc) over f1 score and accuracy in binary classification evaluation," BMC genomics, vol. 21, no. 1, pp. 1-13, 2020.
[16] J. Brownlee, Deep learning for time series forecasting: predict the future with MLPs, CNNs and LSTMs in Python. Machine Learning Mastery, 2018.
[17] I. Sharafaldin, A. H. Lashkari, and A. A. Ghorbani, "Toward generating a new intrusion detection dataset and intrusion traffic characterization." ICISSp, vol. 1, pp. 108-116, 2018.
[18] N. Moustafa and J. Slay, "Unsw-nb15: a comprehensive data set for network intrusion detection systems (unsw-nb15 network data set)," in 2015 military communications and information systems conference (MilCIS). IEEE, 2015, pp. 1-6.
[19] P. J. Werbos, "Backpropagation through time: what it does and how to do it," Proceedings of the IEEE, vol. 78, no. 10, pp. 1550-1560, 1990.
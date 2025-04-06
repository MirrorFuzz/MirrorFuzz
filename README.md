## This repository contains the source code for "MirrorFuzz: Fuzzing Deep Learning Framework APIs using LLMs and Shared Bugs." 
Some of our code and data are still being organized and will be updated in a few weeks.

[Here is the list of bugs discovered by MirrorFuzz.](https://github.com/MirrorFuzz/MirrorFuzz/blob/main/MirrorFuzz_bug_list.xlsx)
## Shared Bugs in Deep Learning frameworks

![SharedBugs](shared_bug_example.png)
<div style="text-align: center;">
  <img src="shared_bug_example.png" alt="Alt text" width="300"/>
  <p><strong>Figure 1:</strong> This is the image caption.</p>
</div>
Deep Learning (DL) frameworks form the backbone of many AI applications. However, bugs in these frameworks can lead to critical failures, impacting performance, security, and reliability. Despite various bug detection methods, little research has been done on identifying common patterns in APIs across DL frameworks and the risks posed by shared bugs. Many DL frameworks expose similar APIs, which makes them susceptible to analogous bugs that can spread across multiple frameworks.

![MirrorFuzz](MirrorFuzz_overview.png)

## MirrorFuzz Introduction
To address this issue, we present MirrorFuzz, an automated fuzzing tool that exploits shared bugs within and across DL framework APIs. MirrorFuzz operates in three stages:

- Buggy APIs Recognition: It collects historical bug data from various DL frameworks to identify potentially buggy APIs.

- Similar APIs Matching: It identifies similar APIs across different DL frameworks based on their functionalities, parameters, and behaviors.

- Test Case Synthesis: Using large language models (LLMs), it generates test cases to trigger analogous bugs across matched APIs by leveraging shared historical bug data.

We evaluate MirrorFuzz on four popular DL frameworks: TensorFlow, PyTorch, OneFlow, and Jittor. Our experiments show that MirrorFuzz improves code coverage by 39.92% on TensorFlow and 98.20% on PyTorch compared to state-of-the-art methods. Additionally, it uncovers 315 bugs, 262 of which are previously unknown, and contributes to fixing 80 bugs, with 52 assigned CNVD IDs.

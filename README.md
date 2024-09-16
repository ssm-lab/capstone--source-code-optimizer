# Source Code Energy Optimizer

**Developer Names**: Sevhena Walker, Mya Hussain, Ayushi Amin, Tanveer Brar, Nivetha Kuruparan
**Supervisor**: Dr. David Istvan

Date of project start: September 16th 2024

**Project Overview**: The goal of this project is to develop tools to improve the energy efficiency of engineered software through refactoring without altering the intent of the source code.

---

### **Key Features**

1. **Refactoring Library**  
   - Provides automated refactoring tools aimed at optimising code for energy efficiency while preserving its functional behaviour.  
   - Analyses code to identify energy-intensive patterns and recommends or applies energy-saving transformations.  
   - Ensures refactored code remains maintainable and efficient across different platforms.

2. **Python-Specific Refactoring Optimization**  
   - Tailors energy-efficient refactoring strategies based on the specific characteristics of Python.  
   - Provides guidelines and transformations to minimise energy consumption while maintaining code compatibility.  
   - Adapts to the unique performance and energy model of Python.

3. **Reinforcement Learning for Refactoring Preferences**  
   - Utilises reinforcement learning to adapt refactoring strategies based on past performance data.  
   - Continuously improves the refactoring process by learning which transformations lead to the greatest energy savings.  
   - Continuously improves the refactoring process by learning which transformations lead to most technically sustainable (readable) code.

4. **DevOps GitHub Integration**  
   - Integrates with GitHub to automatically trigger energy-efficient refactoring as part of the CI/CD pipeline.  
   - Provides version control, ensuring that refactoring changes can be tracked, tested, and validated before deployment.  
   - Implements an automated feedback loop that records energy consumption data and feeds it back into the library's reinforcement learning model.
   - Automates testing of source code within the DevOps workflow to ensure that behaviour is maintained.

**Nice-to-Have Features:**

1. **Library Plugin**  
   - Offers a plugin extension for popular IDEs and platforms, allowing developers to easily incorporate the refactoring library into their existing workflows.  
   - Provides real-time suggestions and refactoring options within the development environment, enhancing usability and accessibility.  
   - Synchronizes plugin with website allowing developers to view measurements taken in a visual manner (i.e. graphs, tables).

2. **Human-in-the-Loop Reinforcement Learning**  
   - Involves human feedback in the reinforcement learning process to guide the system's refactoring decisions based on developer expertise and preferences.  
   - Balances automated refactoring with human oversight to ensure that complex refactoring decisions align with the project's goals and constraints.


The folders and files for this project are as follows:

docs - Documentation for the project

refs - Reference material used for the project, including papers

src - Source code

test - Test cases

etc.

# **Usability Test Plan for VSCode Extension**

## **Purpose**

The purpose of this usability test is to evaluate the ease of use, efficiency, and overall user experience of the VSCode extension for refactoring Python code to improve energy efficiency. The test will identify usability issues that may hinder adoption by software developers.

## **Objective**

Evaluate the usability of the extension’s **smell detection, refactoring process, customization settings, and refactoring view**.

- Assess how easily developers can navigate the extension interface.
- Measure the efficiency of the workflow when applying or rejecting refactorings.
- Identify areas of confusion or frustration.

## **Methodology**

### **Test Type**

Moderated usability testing.

### **Participants**

- **Target Users**: Python developers who use VSCode.
- **Number of Participants**: 5–7.
- **Recruitment Criteria**:
  - Experience with Python development.
  - Familiarity with VSCode.
  - No prior experience with this extension.

### **Testing Environment**

- **Hardware**: Provided computer.
- **Software**:
  - VSCode (latest stable release).
  - The VSCode extension installed.
  - Screen recording software (optional, for post-test analysis).
  - A sample project with **predefined code snippets** containing various **code smells**.
- **Network Requirements**: Stable internet connection for remote testing.

### **Test Moderator Role**

- Introduce the test and explain objectives.
- Observe user interactions without providing assistance unless necessary.
- Take notes on usability issues, pain points, and confusion.
- Ask follow-up questions after each task.
- Encourage participants to **think aloud**.

## **Task Overview**  

| **Task #** | **Task Description**                                                               | **Moderator Observations & Questions**                                                        | **Success Criteria**                                                               |
| ---------- | ---------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| **1**      | Run a standalone code smell detection on a Python file.                            | Does the user identify the correct way to trigger detection? What do they see?                | User successfully runs the detection without confusion.                            |
| **2**      | Click on a detected smell and observe the text decoration.                         | Does the user notice the displayed smell name?                                                | Smell name appears clearly when the line is selected.                              |
| **3**      | Hover over a detected smell to view additional details and quick refactor options. | Does the user understand the additional information? Do they attempt to use a quick command?  | User successfully interacts with hover details and quick actions.                  |
| **4**      | **Initiate refactoring**                                                           | Does the user understand what will change before applying? Do they see the sidebar pop up?    | The user successfully refactors and verifies the expected changes.                 |
| **5**      | **Refactor a single-file smell**                                                   | What does the user notice? Can they apply a smell successfully?                               | User successfully locates the refactoring view.                                    |
| **6**      | **Refactor a multi-file smell** that modifies multiple related files.              | Does the user understand that multiple files will be affected?                                | User correctly applies the refactoring and inspects all modified files.            |
| **7**      | **Customize extension settings** to enable/disable specific smells.                | Does the user navigate to settings easily? Do they understand the impact of disabling smells? | User successfully customizes settings and observes the expected detection changes. |
| **8**      | **Final Feedback**: Share thoughts on usability, clarity, and overall experience.  | What features were easy or difficult to use? Did any steps feel unclear?                      | User fills out survey                                                              |

---

## **Metrics for Evaluation**

- **Task Completion Rate**: % of users successfully completing each task.
- **Time on Task**: Average time taken to complete each step.
- **Error Rate**: Number of failed attempts or incorrect actions.
- **User Confidence Score**: Self-reported ease of use (1-5 scale).
- **Qualitative Feedback**: Key comments or confusion points.

## **Data Collection**

### **Metrics**

- **Task Success Rate**: % of users who complete tasks without assistance.
- **Time on Task**: Time taken to complete each task.
- **Error Rate**: Number of errors or missteps per task.
- **User Satisfaction**: Post-test rating on a scale of 1–5.

### **Qualitative Data**

- Observations of confusion, hesitation, or frustration.
- Participant comments and feedback.
- Follow-up questions about expectations vs. actual experience.
- Pre-test survey.
- Post-test survey.

## **Analysis and Reporting**

- Identify common pain points and recurring issues.
- Categorize usability issues by severity:
  - **Critical**: Blocks users from completing tasks.
  - **Major**: Causes significant frustration but has workarounds.
  - **Minor**: Slight inconvenience, but doesn't impact core functionality.
- Provide recommendations for UI/UX improvements.
- Summarize key findings and next steps.

## **Next Steps**

- Fix major usability issues before release.
- Conduct follow-up usability tests if significant changes are made.
- Gather further feedback from real users post-release.

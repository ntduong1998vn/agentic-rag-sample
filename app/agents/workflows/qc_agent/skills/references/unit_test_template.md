# Manual Unit Test Case Template

This template provides a standardized tabular format for documenting manual unit test cases.

---

## Template Structure

| TC ID | Feature | Test Scenario | Preconditions | Test Steps | Test Data | Expected Result | Priority | Status |
|-------|---------|---------------|---------------|------------|-----------|-----------------|----------|--------|
| TC_XXX_001 | Feature name | What is being tested | System state before test | 1. Step one<br>2. Step two<br>3. Step three | Input values and data | What should happen | High/Medium/Low | - |

---

## Column Definitions

### TC ID (Test Case ID)
- **Format:** `TC_<Module>_<Number>`
- **Example:** `TC_AUTH_001`, `TC_PAYMENT_015`
- **Purpose:** Unique identifier for traceability

### Feature
- **What:** Name of the feature/module being tested
- **Example:** "User Login", "Password Reset", "Order Checkout"

### Test Scenario
- **What:** Specific scenario or condition being tested
- **Example:** "Valid credentials", "Invalid email format", "Expired session"

### Preconditions
- **What:** Required system state or setup before executing test
- **Example:** 
  - "User account exists in database"
  - "User is logged in"
  - "Shopping cart has 3 items"

### Test Steps
- **What:** Sequential actions to perform the test
- **Format:** Numbered list, use `<br>` for line breaks in markdown tables
- **Example:**
  ```
  1. Navigate to login page<br>2. Enter email<br>3. Enter password<br>4. Click Submit button
  ```

### Test Data
- **What:** Specific input values used in the test
- **Format:** Key-value pairs or inline format
- **Example:**
  - "email: test@example.com, password: Pass123!"
  - "amount: $100.50, currency: USD"

### Expected Result
- **What:** Expected outcome after executing test steps
- **Be Specific:** Include UI changes, messages, data changes, navigation
- **Example:**
  - "User redirected to dashboard, welcome message displayed"
  - "Error message: 'Invalid email format'"

### Priority
- **Values:** High, Medium, Low
- **Criteria:**
  - **High:** Critical functionality, blocks other features
  - **Medium:** Important but has workarounds
  - **Low:** Nice to have, cosmetic issues

### Status
- **Values:** 
  - `-` (Not executed)
  - `Pass` (Test passed)
  - `Fail` (Test failed)
  - `Blocked` (Cannot test due to dependency)
- **Usage:** Filled by QA tester during execution

---

## Example: Complete Test Case Table

### Feature: User Authentication

| TC ID | Feature | Test Scenario | Preconditions | Test Steps | Test Data | Expected Result | Priority | Status |
|-------|---------|---------------|---------------|------------|-----------|-----------------|----------|--------|
| TC_AUTH_001 | Login | Valid credentials | User exists in system | 1. Open login page<br>2. Enter email<br>3. Enter password<br>4. Click "Login" | email: john@test.com<br>password: Valid123! | Redirect to dashboard, display "Welcome John" | High | - |
| TC_AUTH_002 | Login | Invalid email format | None | 1. Open login page<br>2. Enter invalid email<br>3. Click "Login" | email: notanemail<br>password: Valid123! | Error: "Please enter a valid email address", remain on login page | High | - |
| TC_AUTH_003 | Login | Incorrect password | User exists | 1. Open login page<br>2. Enter valid email<br>3. Enter wrong password<br>4. Click "Login" | email: john@test.com<br>password: WrongPass | Error: "Invalid credentials", remain on login page, password field cleared | High | - |
| TC_AUTH_004 | Login | Empty password | User exists | 1. Open login page<br>2. Enter email<br>3. Leave password empty<br>4. Click "Login" | email: john@test.com<br>password: (empty) | Error: "Password is required", Login button disabled | Medium | - |
| TC_AUTH_005 | Login | Account locked | User exists, account locked | 1. Open login page<br>2. Enter valid credentials<br>3. Click "Login" | email: locked@test.com<br>password: Valid123! | Error: "Account locked due to multiple failed attempts. Contact support." | High | - |

---

## Tips for Writing Test Cases

### 1. Be Specific and Measurable
- ❌ Bad: "System works correctly"
- ✅ Good: "Order status changes to 'Confirmed', email sent to user@test.com"

### 2. Use Consistent Formatting
- Keep Test Steps numbered and sequential
- Use `<br>` tags for multi-line content in table cells
- Use consistent terminology (e.g., "Click" vs "Press")

### 3. Include Boundary Values
- Test minimum, maximum, and edge values
- Example: 8 chars (min), 128 chars (max), empty string

### 4. Cover Positive and Negative Paths
- Not just happy path - test error conditions too
- Include invalid inputs, unauthorized access, edge cases

### 5. Make Test Data Realistic
- Use realistic but fake data (test@example.com, not real emails)
- Include special characters where relevant

### 6. One Scenario Per Test Case
- Don't combine multiple scenarios in one test case
- Keep each test focused and independent

---

## Usage Instructions

1. **Copy the table structure** from the "Template Structure" section above
2. **Fill in each column** following the column definitions
3. **Group by Feature** - create separate tables for different features/modules
4. **Number sequentially** - TC_MODULE_001, TC_MODULE_002, etc.
5. **Review for completeness** - ensure all POVs are covered where applicable

---

**Note:** This template is for **manual test cases** (executed by QA testers), not automated test scripts.

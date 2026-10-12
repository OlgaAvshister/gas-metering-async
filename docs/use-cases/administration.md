# Use cases: Administrator

## UC-16. Creating a user and assigning a role

**Goal.** Register a new user with the appropriate access rights.

**Precondition.** The administrator is signed in.

**Main scenario**

1. The administrator opens user management.
2. The administrator presses "create user".
3. The administrator fills in the login, full name and contact details.
4. The administrator picks a role: Dispatcher, Accounting engineer, Counterparty
   representative, Financial controller, Administrator, IT operations, Laboratory
   technician, Regulator.
5. Where needed, the administrator adds further restrictions: for the
   Counterparty representative role, binding to a specific delivery point as set
   by contract.
6. The administrator saves the user.
7. The system creates the account and sends an invitation by e-mail with
   instructions for setting a password.

**Result.** The user exists and can sign in with the appropriate rights.

**Extensions**

- **6a.** A user with that login already exists:
  1. The system shows an error and asks for a different login.
  2. The scenario returns to step 3.
- **7a.** The administrator withdraws the invitation before it is used:
  1. The system blocks the account.
  2. The use case ends.

## UC-17. Blocking and unblocking an account

**Goal.** Block a user's access, on departure for instance, or unblock it when
needed.

**Precondition.** The administrator is signed in.

**Main scenario**

1. The administrator opens user management.
2. The administrator finds the user in the list.
3. The administrator chooses "block" or "unblock".
4. The system confirms the action and changes the account status.

**Result.** The account is blocked or unblocked.

**Extensions**

- **2a.** The user is not found:
  1. The system shows "no users found".
  2. The administrator changes the search; the scenario returns to step 2.
- **4a.** On blocking, the user has an active session:
  1. The system ends the session by force rather than waiting for it to expire.
  2. The system refuses any further sign-in.
  3. The use case ends.

## UC-18. Reviewing the audit journal of user actions

**Goal.** Review the history of user actions, to detect breaches or investigate
incidents.

**Precondition.** The administrator is signed in.

**Main scenario**

1. The administrator opens the audit journal.
2. The administrator sets filters: user, period, type of action.
3. The system shows the entries with time, user, type of action, object, IP
   address and outcome.
4. The administrator reviews them and exports the journal if needed.

**Result.** The administrator has the information needed for oversight and
investigation.

**Extensions**

- **2a.** No filters are set:
  1. The system shows all entries for the last 24 hours.
  2. The scenario continues at step 4.
- **4a.** The administrator needs the journal for an arbitrary period:
  1. The administrator sets the period and exports the journal.
  2. The system produces the file.
  3. The use case ends.

## UC-19. Maintaining reference data

**Goal.** Update the system's reference data — coefficients, methods — so that
future calculations are correct.

**Precondition.** The administrator is signed in.

**Main scenario**

1. The administrator opens the reference data section.
2. The administrator picks the type: coefficients, methods, or contract
   parameters.
3. For coefficients and methods: the administrator adds a new version with the
   date it takes effect.
4. For contract parameters: the administrator can view but not edit. In the MVP,
   changes come only through integration or upload.
5. The system stores the new version and records the change in the audit journal.

**Result.** Reference data is updated and future calculations use it.

**Extensions**

- **4a.** The administrator tries to change a contract parameter through the
  interface:
  1. The system blocks the action and shows "changing contract parameters is not
     supported in the MVP".
  2. The use case ends.

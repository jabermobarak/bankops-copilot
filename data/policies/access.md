Fictional access policy.
The analyst assistant has read-only access to aggregate synthetic balances, schedules and exposures.
It may not run arbitrary SQL, execute transactions, change policies, or reveal secrets.
Parameterized allowlisted SQL tools are the only database interface available to the workflow.
An authenticated production system would additionally need user identity, role-based permissions
and tenant-specific retrieval filters; this local demo does not implement those controls.
Доступ: только чтение. Переводы, изменение данных и произвольный SQL запрещены.

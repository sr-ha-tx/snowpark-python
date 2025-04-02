# Working with Imported Database

## Granting Privileges on an imported database

### Objects in Share not associated with database role.
Allow Users to access objects in share by granting the **IMPORTED PRIVILEGES** privilege on an imported database to one or more of your roles.  
A role can only grant IMPORTED PRIVILEGES only when either
- owns the imported database  
- was granted MANAGE GRANTS global privilege

### Objects in a share associated with a database role
Allow users to access objects in a share by granting the appropriate database role in the imported database to one or more roles in your account.  
```
SHOW DATABASE ROLES IN DATABASE c1;
GRANT DATABASE ROLE c1.r1 TO ROLE analyst;
```


# Users Table Guide - Staff and User Queries

## Table Information

**Table Name**: `users`

## Important Columns

- `id` - Primary key
- `email` - User email address
- `first_name` - User's first name
- `last_name` - User's last name
- `is_staff` - **BOOLEAN: 1 = staff user, 0 = regular user**
- `active` - Whether user is active
- `confirmed` - Whether user is confirmed
- `home_dealership_id` - User's primary dealership
- `created_at` - When user was created
- `updated_at` - When user was last updated
- `deleted_at` - Soft delete timestamp (NULL = not deleted)

## Common Queries

### Count Staff Users
```sql
SELECT COUNT(*) as total FROM users WHERE is_staff = 1 AND deleted_at IS NULL
```

### Count All Users
```sql
SELECT COUNT(*) as total FROM users WHERE deleted_at IS NULL
```

### Count Non-Staff Users
```sql
SELECT COUNT(*) as total FROM users WHERE is_staff = 0 AND deleted_at IS NULL
```

### Count Active Staff Users
```sql
SELECT COUNT(*) as total FROM users WHERE is_staff = 1 AND active = 1 AND deleted_at IS NULL
```

## Query Patterns

When user asks:
- "How many staff users" → Query `users` WHERE `is_staff = 1`
- "How many users" → Query `users` table
- "How many employees" → Query `users` WHERE `is_staff = 1`
- "Count staff" → Query `users` WHERE `is_staff = 1`
- "Total staff members" → Query `users` WHERE `is_staff = 1`

## Example Results

- **Total users**: 78
- **Staff users**: 42  
- **Non-staff users**: 36

## Related Tables

- `role_user` - Maps users to roles
- `dealership_user` - Maps users to dealerships
- `team_user` - Maps users to teams

## Important Notes

1. **Always check `deleted_at IS NULL`** for active records
2. **`is_staff = 1`** means staff user, **`is_staff = 0`** means regular user
3. Use `active = 1` if you need to filter for only active users
4. Staff users are employees/administrators, non-staff are typically customers


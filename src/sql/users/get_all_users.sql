SELECT id, username, email, is_active
FROM users
ORDER BY id
LIMIT :limit OFFSET :offset;
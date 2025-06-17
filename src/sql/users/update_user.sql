UPDATE users
SET username = :username,
    email = :email,
    is_active = :is_active
WHERE id = :user_id;
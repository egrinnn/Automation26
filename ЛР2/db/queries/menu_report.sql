SELECT d.name AS dish, c.name AS category, d.price
FROM dishes d
JOIN categories c ON c.id = d.category_id
WHERE d.is_available = TRUE
ORDER BY c.name, d.name;

SELECT m.menu_date, d.name, d.price
FROM menus m
JOIN menu_items mi ON mi.menu_id = m.id
JOIN dishes d ON d.id = mi.dish_id
WHERE m.status = 'published'
ORDER BY m.menu_date DESC, mi.display_order;

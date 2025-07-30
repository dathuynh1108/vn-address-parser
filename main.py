from parser import parse_address

parsed = parse_address("123 Xuân Thủy, Phú Nhuận, TP. Hồ Chí Minh")
print(parsed)


parsed = parse_address("123 Xuân Thủy, Châu Thành, Tiền Giang")
print(parsed)
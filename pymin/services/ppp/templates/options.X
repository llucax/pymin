% if conn.type == 'PPP':
lock ${conn.device}
% elif conn.type == 'OE':
lock plugin rp-pppoe.so ${conn.device}
% elif conn.type == 'TUNNEL':
lock noauth nobsdcomp nodeflate
% endif
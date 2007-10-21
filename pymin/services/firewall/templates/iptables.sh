#!/bin/sh

<%!

# TODO escape shell commands more securely
def s(text):
    return repr(text.encode('utf-8'))

def optional(switch, value):
    if value is not None:
        return '%s %s' % (switch, s(value))
    return ''

%>

/usr/sbin/iptables -t filter -F

/usr/sbin/iptables -t filter -P INPUT ACCEPT
/usr/sbin/iptables -t filter -P OUTPUT ACCEPT
/usr/sbin/iptables -t filter -P FORWARD ACCEPT

% for (index, rule) in enumerate(rules):
/usr/sbin/iptables -t filter \
    -I ${rule.chain|s} ${index+1|s} \
    -j ${rule.target|s} \
    ${optional('-s', rule.src)} \
    ${optional('-d', rule.dst)} \
    ${optional('-p', rule.protocol)} \
    ${optional('-m', rule.protocol)} \
    ${optional('--sport', rule.src_port)} \
    ${optional('--dport', rule.dst_port)}

%endfor

<%doc> vim: set filetype=python sw=4 sts=4 et : </%doc>

#!/bin/bash
# XRAY批量配置脚本
# 支持VMESS和SOCKS5协议，自动映射出站IP

RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[36m"
PLAIN='\033[0m'

NAME="xray"
CONFIG_FILE="/usr/local/etc/${NAME}/config.json"
SERVICE_FILE="/etc/systemd/system/${NAME}.service"
DEFAULT_VMESS_PORT=20000
DEFAULT_SOCKS_PORT=30000

# 获取网卡绑定的所有IP地址
IP_ADDRESSES=($(hostname -I | tr ' ' '\n' | sort -u | grep -v '^127.' | grep -v '^::1' | tr '\n' ' '))
TOTAL_IPS=${#IP_ADDRESSES[@]}

declare -a PROTOCOLS PORTS UUIDS OUTBOUND_IPS LINKS

colorEcho() {
    echo -e "${1}${@:2}${PLAIN}"
}

checkSystem() {
    result=$(id | awk '{print $1}')
    if [[ $result != "uid=0(root)" ]]; then
        colorEcho $RED "请以root身份执行该脚本"
        exit 1
    fi

    if ! command -v xray &> /dev/null; then
        colorEcho $YELLOW "未检测到XRAY，正在安装..."
        bash -c "$(curl -s -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" > /dev/null 2>&1
        colorEcho $GREEN "XRAY安装完成"
    fi

    res=`which jq 2>/dev/null`
    if [[ "$?" != "0" ]]; then
        if [[ -x "$(command -v apt)" ]]; then
            apt install -y jq > /dev/null 2>&1
        elif [[ -x "$(command -v yum)" ]]; then
            yum install -y jq > /dev/null 2>&1
        else
            colorEcho $RED "无法安装必要依赖jq，请手动安装"
            exit 1
        fi
    fi
}

# 开放端口
    openPort() {
        local port=$1
        if [ -x "$(command -v firewall-cmd)" ]; then
            firewall-cmd --permanent --add-port=${port}/tcp > /dev/null 2>&1
            firewall-cmd --permanent --add-port=${port}/udp > /dev/null 2>&1
            firewall-cmd --reload > /dev/null 2>&1
        elif [ -x "$(command -v ufw)" ]; then
            ufw allow ${port}/tcp > /dev/null 2>&1
            ufw allow ${port}/udp > /dev/null 2>&1
            ufw reload > /dev/null 2>&1
        fi
    }

    # 显示链接
    displayLinks() {
        local proto=$1
        colorEcho $YELLOW "\n===== ${proto}节点链接 ====="
        for link in "${LINKS[@]}"; do
            echo -e "${GREEN}${link}${PLAIN}"
        done
        colorEcho $YELLOW "=========================\n"
        colorEcho $BLUE "链接已显示在SSH界面，可直接复制使用"
    }

    # 生成VMESS链接
    generateVMESSLink() {
    local ip=$1
    local port=$2
    local uuid=$3
    local security="auto"
    local network="tcp"
    local type="none"

    # VMESS链接格式: vmess://base64(json)
    local vmess_json=$(jq -n --arg v "2" --arg ps "VMESS_${ip}_${port}" --arg add "$ip" --arg port "$port" --arg id "$uuid" --arg aid "0" --arg net "$network" --arg type "$type" --arg host "" --arg path "" --arg tls "" '{
        v: $v,
        ps: $ps,
        add: $add,
        port: $port,
        id: $id,
        aid: $aid,
        net: $net,
        type: $type,
        host: $host,
        path: $path,
        tls: $tls
    }')

    echo -n "vmess://"$(echo -n "$vmess_json" | base64 -w 0)
}

mainMenu() {
    clear
    colorEcho $BLUE "======================================"
    colorEcho $BLUE "          XRAY批量配置工具             "
    colorEcho $BLUE "======================================"
    colorEcho $YELLOW "检测到网卡绑定的IP地址:"
    for ((i=0; i<TOTAL_IPS; i++)); do
        colorEcho $GREEN "  $((i+1)). ${IP_ADDRESSES[$i]}"
    done
    echo ""
    colorEcho $YELLOW "请选择要创建的节点类型:"
    colorEcho $GREEN "  1. 创建VMESS节点"
    colorEcho $GREEN "  2. 创建SOCKS5节点"
    colorEcho $RED "  0. 退出"
    echo ""
    read -p "请输入选择 [0-2]: " choice
    
    case $choice in
        1)
            read -p "请输入VMESS起始端口 (默认: $DEFAULT_VMESS_PORT): " start_port
            start_port=${start_port:-$DEFAULT_VMESS_PORT}
            generateVMESSConfig $start_port
            ;;
        2)
            read -p "请输入SOCKS5起始端口 (默认: $DEFAULT_SOCKS_PORT): " start_port
            start_port=${start_port:-$DEFAULT_SOCKS_PORT}
            generateSOCKSConfig $start_port
            ;;
        0)
            colorEcho $BLUE "感谢使用，再见！"
            exit 0
            ;;
        *)
            colorEcho $RED "无效选择，请重试"
            sleep 2
    mainMenu
            ;;
    esac
}

# 生成VMESS配置
generateVMESSConfig() {
    local start_port=$1
    local config_json=
    local inbound_entries=

    # 备份现有配置
    if [[ -f $CONFIG_FILE ]]; then
        cp $CONFIG_FILE ${CONFIG_FILE}.bak
    fi

    # 创建基础配置结构
    config_json=$(jq -n '{"log": {"loglevel": "warning"}, "inbounds": [], "outbounds": []}')

    # 添加出站配置
    for ((i=0; i<TOTAL_IPS; i++)); do
        local ip=${IP_ADDRESSES[$i]}
        config_json=$(echo "$config_json" | jq --arg tag "outbound_$i" --arg ip "$ip" '.outbounds += [{"protocol": "freedom", "tag": $tag, "settings": {"domainStrategy": "UseIP"}, "streamSettings": {"sockopt": {"interface": $ip}}}]')
    done

    # 添加入站配置
    for ((i=0; i<TOTAL_IPS; i++)); do
        local port=$((start_port + i))
        local ip=${IP_ADDRESSES[$i]}
        local uuid=$(/usr/local/bin/xray uuid)
        local tag="inbound_vmess_$i"

        # 生成inbound配置
        inbound_config=$(jq -n --arg port $port --arg uuid "$uuid" --arg tag "$tag" '
            {
                "port": $port,
                "protocol": "vmess",
                "tag": $tag,
                "settings": {
                    "clients": [{
                        "id": $uuid,
                        "alterId": 0
                    }],
                    "decryption": "none"
                },
                "streamSettings": {
                    "network": "tcp",
                    "tcpSettings": {
                        "header": {
                            "type": "none"
                        }
                    }
                },
                "sniffing": {
                    "enabled": true,
                    "destOverride": ["http", "tls"]
                },
                "routing": {
                    "domainStrategy": "IPOnDemand",
                    "rules": [{
                        "type": "field",
                        "outboundTag": "outbound_$i",
                        "inboundTag": ["$tag"]
                    }]
                }
            }
        ')

        config_json=$(echo "$config_json" | jq --argjson inbound "$inbound_config" '.inbounds += [$inbound]')

        # 生成SOCKS链接
        local socks_link="socks5://${username}:${password}@${ip}:${port}?udp=true"
        LINKS+=("$socks_link")

        # 开放端口
        openPort $port

        colorEcho $BLUE "已创建SOCKS5节点: $ip:$port (出站IP: ${IP_ADDRESSES[$i]})"
    done

    # 保存配置文件
    echo "$config_json" | jq . > $CONFIG_FILE

    # 重启XRAY
    systemctl restart xray > /dev/null 2>&1
    sleep 2

    # 显示生成的链接
    displayLinks "SOCKS5"

        # 生成VMESS链接
        local vmess_link=$(generateVMESSLink "$ip" "$port" "$uuid")
        LINKS+=("$vmess_link")

        # 开放端口
        openPort $port

        colorEcho $BLUE "已创建VMESS节点: $ip:$port (出站IP: ${IP_ADDRESSES[$i]})"
    done

    # 保存配置文件
    echo "$config_json" | jq . > $CONFIG_FILE

    # 重启XRAY
    systemctl restart xray > /dev/null 2>&1
    sleep 2

    # 显示生成的链接
    displayLinks() {
    local proto=$1
    colorEcho $YELLOW "\n===== ${proto}节点链接 ====="
    for link in "${LINKS[@]}"; do
        echo -e "${GREEN}${link}${PLAIN}"
    done
    colorEcho $YELLOW "=========================\n"
    colorEcho $BLUE "链接已显示在SSH界面，可直接复制使用"
}
    displayLinks "VMESS"
}

# 生成SOCKS5配置
generateSOCKSConfig() {
    local start_port=$1
    local config_json=
    local inbound_entries=

    # 备份现有配置
    if [[ -f $CONFIG_FILE ]]; then
        cp $CONFIG_FILE ${CONFIG_FILE}.bak
    fi

    # 创建基础配置结构
    config_json=$(jq -n '{"log": {"loglevel": "warning"}, "inbounds": [], "outbounds": []}')

    # 添加出站配置
    for ((i=0; i<TOTAL_IPS; i++)); do
        local ip=${IP_ADDRESSES[$i]}
        config_json=$(echo "$config_json" | jq --arg tag "outbound_$i" --arg ip "$ip" '.outbounds += [{"protocol": "freedom", "tag": $tag, "settings": {"domainStrategy": "UseIP"}, "streamSettings": {"sockopt": {"interface": $ip}}}]')
    done

    # 添加入站配置
    for ((i=0; i<TOTAL_IPS; i++)); do
        local port=$((start_port + i))
        local ip=${IP_ADDRESSES[$i]}
        local tag="inbound_socks_$i"
        local username=$(openssl rand -hex 8)
        local password=$(openssl rand -hex 10)

        # 生成inbound配置
        inbound_config=$(jq -n --arg port $port --arg tag "$tag" --arg username "$username" --arg password "$password" '
            {
                "port": $port,
                "protocol": "socks",
                "tag": $tag,
                "settings": {
                    "auth": "password",
                    "accounts": [{
                        "user": $username,
                        "pass": $password
                    }],
                    "udp": true,
                    "ip": "0.0.0.0"
                },
                "routing": {
                    "domainStrategy": "IPOnDemand",
                    "rules": [{
                        "type": "field",
                        "outboundTag": "outbound_$i",
                        "inboundTag": ["$tag"]
                    }]
                }
            }
        ')

        config_json=$(echo "$config_json" | jq --argjson inbound "$inbound_config" '.inbounds += [$inbound]')

        # 生成SOCKS链接
        local socks_link="socks5://${username}:${password}@${ip}:${port}?udp=true"
        LINKS+=("$socks_link")

        # 开放端口
        openPort $port

        colorEcho $BLUE "已创建SOCKS5节点: $ip:$port (出站IP: ${IP_ADDRESSES[$i]})"
    done

    # 保存配置文件
    echo "$config_json" | jq . > $CONFIG_FILE

    # 重启XRAY
    systemctl restart xray > /dev/null 2>&1
    sleep 2

    # 显示生成的链接
    displayLinks "SOCKS5"
}
    local start_port=$1

    # 备份现有配置
    if [[ -f $CONFIG_FILE ]]; then
        cp $CONFIG_FILE ${CONFIG_FILE}.bak
    fi

    # 创建基础配置结构
    config_json=$(jq -n '{"log": {"loglevel": "warning"}, "inbounds": [], "outbounds": []}')

    # 添加出站配置
    for ((i=0; i<TOTAL_IPS; i++)); do
        local ip=${IP_ADDRESSES[$i]}
        config_json=$(echo "$config_json" | jq --arg tag "outbound_$i" --arg ip "$ip" '.outbounds += [{"protocol": "freedom", "tag": $tag, "settings": {"domainStrategy": "UseIP"}, "streamSettings": {"sockopt": {"interface": $ip}}}]')
    done

    # 添加入站配置
    for ((i=0; i<TOTAL_IPS; i++)); do
        local port=$((start_port + i))
        local ip=${IP_ADDRESSES[$i]}
        local tag="inbound_socks_$i"
        local username=$(openssl rand -hex 8)
        local password=$(openssl rand -hex 10)

        # 生成inbound配置
        inbound_config=$(jq -n --arg port $port --arg tag "$tag" --arg username "$username" --arg password "$password" '
            {
                "port": $port,
                "protocol": "socks",
                "tag": $tag,
                "settings": {
                    "auth": "password",
                    "accounts": [{
                        "user": $username,
                        "pass": $password
                    }],
                    "udp": true,
                    "ip": "0.0.0.0"
                },
                "routing": {
                    "domainStrategy": "IPOnDemand",
                    "rules": [{
                        "type": "field",
                        "outboundTag": "outbound_'"$i"'",
                        "inboundTag": [$tag]
                    }]
                }
            }
        ')

        config_json=$(echo "$config_json" | jq --argjson inbound
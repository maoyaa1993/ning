#!/bin/bash
# Xray VMESS+KCP+DTLS 和 SOCKS5 批量部署脚本
# Author: 基于原Reality脚本修改

RED="\033[31m"      # Error message
GREEN="\033[32m"    # Success message
YELLOW="\033[33m"   # Warning message
BLUE="\033[36m"     # Info message
PLAIN='\033[0m'

NAME="xray"
CONFIG_FILE="/usr/local/etc/${NAME}/config.json"
SERVICE_FILE="/etc/systemd/system/${NAME}.service"
DEFAULT_VMESS_START_PORT=20000
DEFAULT_SOCKS5_START_PORT=30000
IP_ADDRESSES=($(hostname -I))
declare -a USER_UUID VMESS_PORT USER_NAME SOCKS5_PORT SOCKS5_USER SOCKS5_PASS

colorEcho() {
    echo -e "${1}${@:2}${PLAIN}"
}

checkSystem() {
    result=$(id | awk '{print $1}')
    if [[ $result != "uid=0(root)" ]]; then
        colorEcho $RED " 请以root身份执行该脚本"
        exit 1
    fi

    res=`which yum 2>/dev/null`
    if [[ "$?" != "0" ]]; then
        res=`which apt 2>/dev/null`
        if [[ "$?" != "0" ]]; then
            colorEcho $RED " 不受支持的Linux系统"
            exit 1
        fi
        PMT="apt"
        CMD_INSTALL="apt install -y "
        CMD_REMOVE="apt remove -y "
        CMD_UPGRADE="apt update; apt upgrade -y; apt autoremove -y"
    else
        PMT="yum"
        CMD_INSTALL="yum install -y "
        CMD_REMOVE="yum remove -y "
        CMD_UPGRADE="yum update -y"
    fi
    res=`which systemctl 2>/dev/null`
    if [[ "$?" != "0" ]]; then
        colorEcho $RED " 系统版本过低，请升级到最新版本"
        exit 1
    fi
}

status() {
    export PATH=/usr/local/bin:$PATH
    cmd="$(command -v xray)"
    if [[ "$cmd" = "" ]]; then
        echo 0
        return
    fi
    if [[ ! -f $CONFIG_FILE ]]; then
        echo 1
        return
    fi
    port=`grep -o '"port": [0-9]*' $CONFIG_FILE | awk '{print $2}' | head -n 1`
    if [[ -n "$port" ]]; then
        res=`ss -ntlp| grep ${port} | grep xray`
        if [[ -z "$res" ]]; then
            echo 2
        else
            echo 3
        fi
    else
        echo 2
    fi
}

statusText() {
    res=`status`
    case $res in
        2)
            echo -e ${GREEN}已安装xray${PLAIN} ${RED}未运行${PLAIN}
            ;;
        3)
            echo -e ${GREEN}已安装xray${PLAIN} ${GREEN}正在运行${PLAIN}
            ;;
        *)
            echo -e ${RED}未安装xray${PLAIN}
            ;;
    esac
}

preinstall() {
    $PMT clean all
    [[ "$PMT" = "apt" ]] && $PMT update
    echo ""
    echo "安装必要软件，请等待..."
    if [[ "$PMT" = "apt" ]]; then
        res=`which ufw 2>/dev/null`
        [[ "$?" != "0" ]] && $CMD_INSTALL ufw
    fi
    res=`which curl 2>/dev/null`
    [[ "$?" != "0" ]] && $CMD_INSTALL curl
    res=`which openssl 2>/dev/null`
    [[ "$?" != "0" ]] && $CMD_INSTALL openssl
    res=`which qrencode 2>/dev/null`
    [[ "$?" != "0" ]] && $CMD_INSTALL qrencode
    res=`which jq 2>/dev/null`
    [[ "$?" != "0" ]] && $CMD_INSTALL jq

    if [[ -s /etc/selinux/config ]] && grep 'SELINUX=enforcing' /etc/selinux/config; then
        sed -i 's/SELINUX=enforcing/SELINUX=permissive/g' /etc/selinux/config
        setenforce 0
    fi
}

installXray() {
    echo ""
    echo "正在安装Xray..."
    bash -c "$(curl -s -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" > /dev/null 2>&1
    colorEcho $BLUE "xray内核已安装完成"
    sleep 5
}

updateXray() {
    echo ""
    echo "正在更新Xray..."
    bash -c "$(curl -s -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" > /dev/null 2>&1
    colorEcho $BLUE "xray内核已更新完成"
    sleep 5
}

removeXray() {
    echo ""
    echo "正在卸载Xray..."
    bash -c "$(curl -s -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ remove --purge > /dev/null 2>&1
    rm -rf /etc/systemd/system/xray.service > /dev/null 2>&1
    rm -rf /etc/systemd/system/xray@.service > /dev/null 2>&1
    rm -rf /usr/local/bin/xray > /dev/null 2>&1
    rm -rf /usr/local/etc/xray > /dev/null 2>&1
    rm -rf /usr/local/share/xray > /dev/null 2>&1
    rm -rf /var/log/xray > /dev/null 2>&1
    colorEcho $RED "已完成xray卸载"
    sleep 5
}

# 生成随机UUID
generate_uuid() {
    cat /proc/sys/kernel/random/uuid
}

# 配置VMESS+KCP+DTLS节点
config_vmess_kcp_dtls() {
    read -p "VMESS起始端口 (默认 $DEFAULT_VMESS_START_PORT): " VMESS_START_PORT
    VMESS_START_PORT=${VMESS_START_PORT:-$DEFAULT_VMESS_START_PORT}
    
    # 开始生成 JSON 配置
    cat > /usr/local/etc/xray/config.json <<EOF
{
    "log": {
        "loglevel": "debug"
    },
    "inbounds": [
EOF

    # 循环遍历 IP 和端口，创建VMESS+KCP+DTLS节点
    for ((i = 0; i < ${#IP_ADDRESSES[@]}; i++)); do
        # 生成随机 UUID
        USER_UUID[$i]=$(generate_uuid)

        # 生成节点名称
        USER_NAME[$i]="VMESS-KCP-DTLS_$i"

        # 开启端口
        VMESS_PORT[$i]=$((VMESS_START_PORT + i))
        echo "正在开启${VMESS_PORT[$i]}端口..."
        if [ -x "$(command -v firewall-cmd)" ]; then
            firewall-cmd --permanent --add-port=${VMESS_PORT[$i]}/udp > /dev/null 2>&1
            firewall-cmd --reload > /dev/null 2>&1
            colorEcho $YELLOW "${VMESS_PORT[$i]}端口已成功开启"
        elif [ -x "$(command -v ufw)" ]; then
            ufw allow ${VMESS_PORT[$i]}/udp > /dev/null 2>&1
            ufw reload > /dev/null 2>&1
            colorEcho $YELLOW "${VMESS_PORT[$i]}端口已成功开启"
        else
            echo "无法配置防火墙规则。请手动配置以确保新xray端口可用!"
        fi

        echo "    {" >> /usr/local/etc/xray/config.json
        echo "      \"port\": ${VMESS_PORT[$i]}," >> /usr/local/etc/xray/config.json
        echo "      \"protocol\": \"vmess\"," >> /usr/local/etc/xray/config.json
        echo "      \"settings\": {" >> /usr/local/etc/xray/config.json
        echo "        \"clients\": [" >> /usr/local/etc/xray/config.json
        echo "          {" >> /usr/local/etc/xray/config.json
        echo "            \"id\": \"${USER_UUID[$i]}\"," >> /usr/local/etc/xray/config.json
        echo "            \"alterId\": 0" >> /usr/local/etc/xray/config.json
        echo "          }" >> /usr/local/etc/xray/config.json
        echo "        ]" >> /usr/local/etc/xray/config.json
        echo "      }," >> /usr/local/etc/xray/config.json
        echo "      \"streamSettings\": {" >> /usr/local/etc/xray/config.json
        echo "        \"network\": \"kcp\"," >> /usr/local/etc/xray/config.json
        echo "        \"security\": \"dtls\"," >> /usr/local/etc/xray/config.json
        echo "        \"kcpSettings\": {" >> /usr/local/etc/xray/config.json
        echo "          \"mtu\": 1350," >> /usr/local/etc/xray/config.json
        echo "          \"tti\": 50," >> /usr/local/etc/xray/config.json
        echo "          \"uplinkCapacity\": 12," >> /usr/local/etc/xray/config.json
        echo "          \"downlinkCapacity\": 100," >> /usr/local/etc/xray/config.json
        echo "          \"congestion\": false," >> /usr/local/etc/xray/config.json
        echo "          \"readBufferSize\": 2," >> /usr/local/etc/xray/config.json
        echo "          \"writeBufferSize\": 2," >> /usr/local/etc/xray/config.json
        echo "          \"header\": {" >> /usr/local/etc/xray/config.json
        echo "            \"type\": \"dtls\"" >> /usr/local/etc/xray/config.json
        echo "          }" >> /usr/local/etc/xray/config.json
        echo "        }," >> /usr/local/etc/xray/config.json
        echo "        \"dtlsSettings\": {" >> /usr/local/etc/xray/config.json
        echo "          \"serverName\": \"\"," >> /usr/local/etc/xray/config.json
        echo "          \"fingerprint\": \"chrome\"" >> /usr/local/etc/xray/config.json
        echo "        }" >> /usr/local/etc/xray/config.json
        echo "      }," >> /usr/local/etc/xray/config.json
        echo "      \"sniffing\": {" >> /usr/local/etc/xray/config.json
        echo "        \"enabled\": true," >> /usr/local/etc/xray/config.json
        echo "        \"destOverride\": [" >> /usr/local/etc/xray/config.json
        echo "          \"http\"," >> /usr/local/etc/xray/config.json
        echo "          \"tls\"," >> /usr/local/etc/xray/config.json
        echo "          \"quic\"" >> /usr/local/etc/xray/config.json
        echo "        ]," >> /usr/local/etc/xray/config.json
        echo "        \"routeOnly\": true" >> /usr/local/etc/xray/config.json
        echo "      }" >> /usr/local/etc/xray/config.json
        if [ $i -lt $((${#IP_ADDRESSES[@]}-1)) ]; then
            echo "    }," >> /usr/local/etc/xray/config.json
        else
            echo "    }" >> /usr/local/etc/xray/config.json
        fi
    done

    # 结束 JSON 配置
    cat >> /usr/local/etc/xray/config.json <<EOF
    ],
    "outbounds": [
        {
            "protocol": "freedom",
            "tag": "direct"
        }
    ]
}
EOF

    restart
    generate_vmess_link
}

# 配置批量SOCKS5节点
config_socks5_batch() {
    read -p "SOCKS5起始端口 (默认 $DEFAULT_SOCKS5_START_PORT): " SOCKS5_START_PORT
    SOCKS5_START_PORT=${SOCKS5_START_PORT:-$DEFAULT_SOCKS5_START_PORT}
    
    read -p "SOCKS5用户名前缀 (默认: user): " SOCKS5_USER_PREFIX
    SOCKS5_USER_PREFIX=${SOCKS5_USER_PREFIX:-"user"}
    
    read -p "SOCKS5密码前缀 (默认: pass): " SOCKS5_PASS_PREFIX
    SOCKS5_PASS_PREFIX=${SOCKS5_PASS_PREFIX:-"pass"}
    
    # 开始生成 JSON 配置
    cat > /usr/local/etc/xray/config.json <<EOF
{
    "log": {
        "loglevel": "debug"
    },
    "inbounds": [
EOF

    # 循环遍历 IP 和端口，创建SOCKS5节点
    for ((i = 0; i < ${#IP_ADDRESSES[@]}; i++)); do
        # 生成用户名和密码
        SOCKS5_USER[$i]="${SOCKS5_USER_PREFIX}${i}"
        SOCKS5_PASS[$i]="${SOCKS5_PASS_PREFIX}${i}"

        # 开启端口
        SOCKS5_PORT[$i]=$((SOCKS5_START_PORT + i))
        echo "正在开启${SOCKS5_PORT[$i]}端口..."
        if [ -x "$(command -v firewall-cmd)" ]; then
            firewall-cmd --permanent --add-port=${SOCKS5_PORT[$i]}/tcp > /dev/null 2>&1
            firewall-cmd --permanent --add-port=${SOCKS5_PORT[$i]}/udp > /dev/null 2>&1
            firewall-cmd --reload > /dev/null 2>&1
            colorEcho $YELLOW "${SOCKS5_PORT[$i]}端口已成功开启"
        elif [ -x "$(command -v ufw)" ]; then
            ufw allow ${SOCKS5_PORT[$i]}/tcp > /dev/null 2>&1
            ufw allow ${SOCKS5_PORT[$i]}/udp > /dev/null 2>&1
            ufw reload > /dev/null 2>&1
            colorEcho $YELLOW "${SOCKS5_PORT[$i]}端口已成功开启"
        else
            echo "无法配置防火墙规则。请手动配置以确保新xray端口可用!"
        fi

        echo "    {" >> /usr/local/etc/xray/config.json
        echo "      \"port\": ${SOCKS5_PORT[$i]}," >> /usr/local/etc/xray/config.json
        echo "      \"protocol\": \"socks\"," >> /usr/local/etc/xray/config.json
        echo "      \"settings\": {" >> /usr/local/etc/xray/config.json
        echo "        \"auth\": \"password\"," >> /usr/local/etc/xray/config.json
        echo "        \"accounts\": [" >> /usr/local/etc/xray/config.json
        echo "          {" >> /usr/local/etc/xray/config.json
        echo "            \"user\": \"${SOCKS5_USER[$i]}\"," >> /usr/local/etc/xray/config.json
        echo "            \"pass\": \"${SOCKS5_PASS[$i]}\"" >> /usr/local/etc/xray/config.json
        echo "          }" >> /usr/local/etc/xray/config.json
        echo "        ]," >> /usr/local/etc/xray/config.json
        echo "        \"udp\": true," >> /usr/local/etc/xray/config.json
        echo "        \"ip\": \"127.0.0.1\"" >> /usr/local/etc/xray/config.json
        echo "      }," >> /usr/local/etc/xray/config.json
        echo "      \"sniffing\": {" >> /usr/local/etc/xray/config.json
        echo "        \"enabled\": true," >> /usr/local/etc/xray/config.json
        echo "        \"destOverride\": [" >> /usr/local/etc/xray/config.json
        echo "          \"http\"," >> /usr/local/etc/xray/config.json
        echo "          \"tls\"," >> /usr/local/etc/xray/config.json
        echo "          \"quic\"" >> /usr/local/etc/xray/config.json
        echo "        ]," >> /usr/local/etc/xray/config.json
        echo "        \"routeOnly\": true" >> /usr/local/etc/xray/config.json
        echo "      }" >> /usr/local/etc/xray/config.json
        if [ $i -lt $((${#IP_ADDRESSES[@]}-1)) ]; then
            echo "    }," >> /usr/local/etc/xray/config.json
        else
            echo "    }" >> /usr/local/etc/xray/config.json
        fi
    done

    # 结束 JSON 配置
    cat >> /usr/local/etc/xray/config.json <<EOF
    ],
    "outbounds": [
        {
            "protocol": "freedom",
            "tag": "direct"
        }
    ]
}
EOF

    restart
    generate_socks5_info
}

# 输出 VMESS 链接
generate_vmess_link() {
    > /root/vmess_link.txt
    colorEcho $BLUE "${BLUE}VMESS+KCP+DTLS订阅链接${PLAIN}："
    
    for ((i = 0; i < ${#IP_ADDRESSES[@]}; i++)); do
        if [[ "${IP_ADDRESSES[$i]}" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            LINK="vmess://$(echo -n "{\"v\":\"2\",\"ps\":\"${USER_NAME[$i]}\",\"add\":\"${IP_ADDRESSES[$i]}\",\"port\":\"${VMESS_PORT[$i]}\",\"id\":\"${USER_UUID[$i]}\",\"aid\":\"0\",\"net\":\"kcp\",\"type\":\"dtls\",\"tls\":\"dtls\",\"fp\":\"chrome\"}" | base64 -w 0)"
        elif [[ "${IP_ADDRESSES[$i]}" =~ ^([0-9a-fA-F:]+)$ ]]; then
            LINK="vmess://$(echo -n "{\"v\":\"2\",\"ps\":\"${USER_NAME[$i]}\",\"add\":\"${IP_ADDRESSES[$i]}\",\"port\":\"${VMESS_PORT[$i]}\",\"id\":\"${USER_UUID[$i]}\",\"aid\":\"0\",\"net\":\"kcp\",\"type\":\"dtls\",\"tls\":\"dtls\",\"fp\":\"chrome\"}" | base64 -w 0)"
        else
            colorEcho $RED "没有获取到有效ip！"
        fi
        colorEcho $YELLOW ${LINK}
        echo ${LINK} >> /root/vmess_link.txt
    done
}

# 输出 SOCKS5 信息
generate_socks5_info() {
    > /root/socks5_info.txt
    colorEcho $BLUE "${BLUE}SOCKS5节点信息${PLAIN}："
    
    for ((i = 0; i < ${#IP_ADDRESSES[@]}; i++)); do
        colorEcho $YELLOW "节点 $((i+1)):"
        colorEcho $YELLOW "  服务器: ${IP_ADDRESSES[$i]}"
        colorEcho $YELLOW "  端口: ${SOCKS5_PORT[$i]}"
        colorEcho $YELLOW "  用户名: ${SOCKS5_USER[$i]}"
        colorEcho $YELLOW "  密码: ${SOCKS5_PASS[$i]}"
        colorEcho $YELLOW "  协议: SOCKS5"
        echo "节点 $((i+1)): ${IP_ADDRESSES[$i]}:${SOCKS5_PORT[$i]} ${SOCKS5_USER[$i]}:${SOCKS5_PASS[$i]}" >> /root/socks5_info.txt
        echo ""
    done
}

start() {
    res=`status`
    if [[ $res -lt 2 ]]; then
        echo -e "${RED}xray未安装，请先安装！${PLAIN}"
        return
    fi
    systemctl restart ${NAME}
    sleep 2
    port=`grep -o '"port": [0-9]*' $CONFIG_FILE | awk '{print $2}' | head -n 1`
    res=`ss -ntlp| grep ${port} | grep xray`
    if [[ "$res" = "" ]]; then
        colorEcho $RED "xray启动失败，请检查端口是否被占用！"
    else
        colorEcho $BLUE "xray启动成功！"
    fi
}

restart() {
    res=`status`
    if [[ $res -lt 2 ]]; then
        echo -e "${RED}xray未安装，请先安装！${PLAIN}"
        return
    fi
    stop
    start
}

stop() {
    res=`status`
    if [[ $res -lt 2 ]]; then
        echo -e "${RED}xray未安装，请先安装！${PLAIN}"
        return
    fi
    systemctl stop ${NAME}
    colorEcho $BLUE "xray停止成功"
}

menu() {
    clear
    echo "##################################################################"
    echo -e "#                   ${RED}Xray 批量部署脚本${PLAIN}                                    #"
    echo -e "# ${GREEN}支持协议${PLAIN}: VMESS+KCP+DTLS, SOCKS5                                    #"
    echo -e "# ${GREEN}多IP支持${PLAIN}: 自动为每个IP创建独立节点                                   #"
    echo "##################################################################"

    echo -e "  ${GREEN}  <Xray内核版本>  ${YELLOW}"
    echo -e "  ${GREEN}1.${PLAIN}  安装xray"
    echo -e "  ${GREEN}2.${PLAIN}  更新xray"
    echo -e "  ${GREEN}3.${RED}  卸载xray${PLAIN}"
    echo " -------------"
    echo -e "  ${GREEN}4.${PLAIN}  搭建VMESS+KCP+DTLS（批量）"
    echo -e "  ${GREEN}5.${PLAIN}  搭建SOCKS5（批量）"
    echo " -------------"
    echo -e "  ${GREEN}6.${PLAIN}  查看VMESS链接"
    echo -e "  ${GREEN}7.${PLAIN}  查看SOCKS5信息"
    echo " -------------"
    echo -e "  ${GREEN}8.${PLAIN}  启动xray"
    echo -e "  ${GREEN}9.${PLAIN}  重启xray"
    echo -e "  ${GREEN}10.${PLAIN}  停止xray"
    echo " -------------"
    echo -e "  ${GREEN}0.${PLAIN}  退出"
    echo -n " 当前xray状态："
    statusText
    echo

    read -p " 请选择操作[0-10]：" answer
    case $answer in
        0)
            exit 0
            ;;
        1)
            checkSystem
            preinstall
            installXray
            menu
            ;;
        2)
            updateXray
            menu
            ;;
        3)
            removeXray
            ;;
        4)
            config_vmess_kcp_dtls
            ;;
        5)
            config_socks5_batch
            ;;
        6)
            if [ -f "/root/vmess_link.txt" ]; then
                cat /root/vmess_link.txt
            else
                colorEcho $RED "未找到VMESS链接文件，请先搭建VMESS节点"
            fi
            ;;
        7)
            if [ -f "/root/socks5_info.txt" ]; then
                cat /root/socks5_info.txt
            else
                colorEcho $RED "未找到SOCKS5信息文件，请先搭建SOCKS5节点"
            fi
            ;;
        8)
            start
            menu
            ;;
        9)
            restart
            menu
            ;;
        10)
            stop
            menu
            ;;
        *)
            echo " 请选择正确的操作！"
            exit 1
            ;;
    esac
}

menu 
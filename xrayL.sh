DEFAULT_SOCKS_START_PORT=20000                   #默认socks起始端口
DEFAULT_VMESS_START_PORT=30000                   #默认vmess起始端口
DEFAULT_SOCKS_USERNAME="userb"                   #默认socks账号
DEFAULT_SOCKS_PASSWORD="passwordb"               #默认socks密码
DEFAULT_WS_PATH="/ws"                            #默认ws路径
DEFAULT_UUID=$(cat /proc/sys/kernel/random/uuid) #默认随机UUID
CONFIG_FILE="/etc/xrayL/config.toml"             #配置文件路径
BACKUP_FILE="/etc/xrayL/config.toml.bak"         #配置备份文件路径
NODE_INFO_FILE="/etc/xrayL/node_info.txt"        #节点信息保存文件

# 获取并按数字顺序排序IP（支持不同网段从小到大）
IP_ADDRESSES=($(hostname -I | tr ' ' '\n' | sort -t . -k 1,1n -k 2,2n -k 3,3n -k 4,4n | tr '\n' ' '))

# 限制最大IP数量（避免配置文件过大导致格式错误）
MAX_IP_COUNT=50
if [ ${#IP_ADDRESSES[@]} -gt $MAX_IP_COUNT ]; then
    IP_ADDRESSES=("${IP_ADDRESSES[@]:0:$MAX_IP_COUNT}")
    echo "警告：IP数量过多，已限制为前$MAX_IP_COUNT个"
fi

# 保存节点信息到文件
save_node_info() {
    local config_type=$1
    local start_port=$2
    local extra_info=$3
    
    # 创建目录（如果不存在）
    mkdir -p /etc/xrayL
    
    # 记录当前时间
    echo "=== $(date "+%Y-%m-%d %H:%M:%S") 生成的$config_type节点信息 ===" >> $NODE_INFO_FILE
    
    # 记录全局信息
    echo "起始端口: $start_port" >> $NODE_INFO_FILE
    echo "结束端口: $((start_port + ${#IP_ADDRESSES[@]} - 1))" >> $NODE_INFO_FILE
    echo "$extra_info" >> $NODE_INFO_FILE
    
    # 记录每个IP对应的端口
    echo "IP与端口对应关系:" >> $NODE_INFO_FILE
    for ((i = 0; i < ${#IP_ADDRESSES[@]}; i++)); do
        local current_port=$((start_port + i))
        echo "${IP_ADDRESSES[i]}: $current_port" >> $NODE_INFO_FILE
    done
    echo "==========================================" >> $NODE_INFO_FILE
    echo "" >> $NODE_INFO_FILE
}

install_xray() {
	echo "安装 Xray..."
	apt-get install unzip -y || yum install unzip -y
	wget https://github.com/XTLS/Xray-core/releases/download/v1.8.3/Xray-linux-64.zip
	unzip Xray-linux-64.zip
	mv xray /usr/local/bin/xrayL
	chmod +x /usr/local/bin/xrayL
	cat <<EOF >/etc/systemd/system/xrayL.service
[Unit]
Description=XrayL Service
After=network.target

[Service]
ExecStart=/usr/local/bin/xrayL -c $CONFIG_FILE
Restart=on-failure
User=nobody
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
	systemctl daemon-reload
	systemctl enable xrayL.service
	systemctl start xrayL.service
	echo "Xray 安装完成."
}

# 生成单一类型配置的函数（严格规范TOML格式）
generate_config() {
	local config_type=$1
	local start_port=$2
	local extra_args=("${@:3}")
	local config_content=""

	for ((i = 0; i < ${#IP_ADDRESSES[@]}; i++)); do
		local current_port=$((start_port + i))
		local tag="tag_${config_type}_$((i + 1))"

		# 生成inbound配置（确保每个[[inbounds]]前有换行）
		config_content+="\n[[inbounds]]\n"
		config_content+="port = $current_port\n"
		config_content+="protocol = \"$config_type\"\n"
		config_content+="tag = \"$tag\"\n"
		config_content+="listen = \"0.0.0.0\"\n"  # 监听所有接口
		config_content+="[inbounds.settings]\n"

		if [ "$config_type" == "socks" ]; then
			local username=${extra_args[0]}
			local password=${extra_args[1]}
			config_content+="auth = \"password\"\n"
			config_content+="udp = true\n"
			config_content+="[[inbounds.settings.accounts]]\n"
			config_content+="user = \"$username\"\n"
			config_content+="pass = \"$password\"\n"
		elif [ "$config_type" == "vmess" ]; then
			local uuid=${extra_args[0]}
			local ws_path=${extra_args[1]}
			config_content+="[[inbounds.settings.clients]]\n"
			config_content+="id = \"$uuid\"\n"
			config_content+="[inbounds.streamSettings]\n"
			config_content+="network = \"ws\"\n"
			config_content+="[inbounds.streamSettings.wsSettings]\n"
			config_content+="path = \"$ws_path\"\n"
		fi

		# 生成outbound配置
		config_content+="\n[[outbounds]]\n"
		config_content+="sendThrough = \"${IP_ADDRESSES[i]}\"\n"
		config_content+="protocol = \"freedom\"\n"
		config_content+="tag = \"$tag\"\n"

		# 生成路由规则
		config_content+="\n[[routing.rules]]\n"
		config_content+="type = \"field\"\n"
		config_content+="inboundTag = \"$tag\"\n"
		config_content+="outboundTag = \"$tag\"\n"
	done

	echo -e "$config_content"
}

config_xray() {
	config_type=$1
	mkdir -p /etc/xrayL
	local new_config=""
	local is_incremental=false

	# 检查是否已有配置文件，如果有则备份并准备增量添加
	if [ -f "$CONFIG_FILE" ]; then
		# 检查配置文件是否有效
		if /usr/local/bin/xrayL test -c "$CONFIG_FILE" >/dev/null 2>&1; then
			cp "$CONFIG_FILE" "$BACKUP_FILE"
			echo "检测到已有配置文件，将在保留原有配置的基础上添加新配置"
			echo "原有配置已备份至 $BACKUP_FILE"
			is_incremental=true
			# 读取现有配置（排除结尾的空行）
			new_config=$(cat "$CONFIG_FILE" | sed '/^$/d')
		else
			echo "检测到无效的配置文件，将创建新配置"
			mv "$CONFIG_FILE" "$CONFIG_FILE.invalid"
			echo "无效配置已重命名为 $CONFIG_FILE.invalid"
		fi
	fi

	# 如果是新配置，添加顶层配置
	if [ "$is_incremental" = false ]; then
		new_config+="[log]\n"
		new_config+="loglevel = \"warning\"\n"
		new_config+="[routing]\n"  # 路由规则的根节点
	fi

	if [ "$config_type" == "socks" ]; then
		read -p "SOCKS 起始端口 (默认 $DEFAULT_SOCKS_START_PORT): " SOCKS_START_PORT
		SOCKS_START_PORT=${SOCKS_START_PORT:-$DEFAULT_SOCKS_START_PORT}
		read -p "SOCKS 账号 (默认 $DEFAULT_SOCKS_USERNAME): " SOCKS_USERNAME
		SOCKS_USERNAME=${SOCKS_USERNAME:-$DEFAULT_SOCKS_USERNAME}
		read -p "SOCKS 密码 (默认 $DEFAULT_SOCKS_PASSWORD): " SOCKS_PASSWORD
		SOCKS_PASSWORD=${SOCKS_PASSWORD:-$DEFAULT_SOCKS_PASSWORD}

		# 生成socks配置
		new_config+=$(generate_config "socks" $SOCKS_START_PORT "$SOCKS_USERNAME" "$SOCKS_PASSWORD")

		# 保存节点信息
		save_node_info "socks" $SOCKS_START_PORT "账号: $SOCKS_USERNAME\n密码: $SOCKS_PASSWORD"

		# 输出结果
		echo ""
		echo "生成 SOCKS 配置完成"
		echo "SOCKS 起始端口: $SOCKS_START_PORT"
		echo "SOCKS 结束端口: $((SOCKS_START_PORT + ${#IP_ADDRESSES[@]} - 1))"
		echo "SOCKS 账号: $SOCKS_USERNAME"
		echo "SOCKS 密码: $SOCKS_PASSWORD"
		echo "节点信息已保存至 $NODE_INFO_FILE"

	elif [ "$config_type" == "vmess" ]; then
		read -p "VMESS 起始端口 (默认 $DEFAULT_VMESS_START_PORT): " VMESS_START_PORT
		VMESS_START_PORT=${VMESS_START_PORT:-$DEFAULT_VMESS_START_PORT}
		read -p "UUID (默认随机): " UUID
		UUID=${UUID:-$DEFAULT_UUID}
		read -p "WebSocket 路径 (默认 $DEFAULT_WS_PATH): " WS_PATH
		WS_PATH=${WS_PATH:-$DEFAULT_WS_PATH}

		# 生成vmess配置
		new_config+=$(generate_config "vmess" $VMESS_START_PORT "$UUID" "$WS_PATH")

		# 保存节点信息
		save_node_info "vmess" $VMESS_START_PORT "UUID: $UUID\nWS 路径: $WS_PATH"

		# 输出结果
		echo ""
		echo "生成 VMESS 配置完成"
		echo "VMESS 起始端口: $VMESS_START_PORT"
		echo "VMESS 结束端口: $((VMESS_START_PORT + ${#IP_ADDRESSES[@]} - 1))"
		echo "UUID: $UUID"
		echo "WS 路径: $WS_PATH"
		echo "节点信息已保存至 $NODE_INFO_FILE"

	else
		echo "类型错误！仅支持socks和vmess."
		exit 1
	fi

	# 写入配置并重启服务
	echo -e "$new_config" > "$CONFIG_FILE"
	
	# 验证配置文件是否有语法错误
	if /usr/local/bin/xrayL test -c "$CONFIG_FILE"; then
		echo "配置文件格式正确，重启服务..."
		systemctl restart xrayL.service
		systemctl --no-pager status xrayL.service
	else
		echo "配置文件存在语法错误！"
		if [ -f "$BACKUP_FILE" ]; then
			echo "正在恢复到之前的配置..."
			mv "$BACKUP_FILE" "$CONFIG_FILE"
			systemctl restart xrayL.service
		fi
		exit 1
	fi
	echo ""
}

main() {
	# 检查xray是否安装，未安装则自动安装
	[ -x "$(command -v xrayL)" ] || install_xray
	
	# 处理命令行参数或用户输入
	if [ $# -eq 1 ]; then
		config_type="$1"
	else
		read -p "选择要生成的节点类型 (socks/vmess): " config_type
	fi
	
	# 验证输入类型
	if [ "$config_type" != "socks" ] && [ "$config_type" != "vmess" ]; then
		echo "错误：仅支持socks和vmess两种类型"
		exit 1
	fi
	
	config_xray "$config_type"
}

main "$@"
    

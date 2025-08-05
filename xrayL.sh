DEFAULT_SOCKS_START_PORT=20000                   #默认socks起始端口
DEFAULT_VMESS_START_PORT=30000                   #默认vmess起始端口
DEFAULT_SOCKS_USERNAME="userb"                   #默认socks账号
DEFAULT_SOCKS_PASSWORD="passwordb"               #默认socks密码
DEFAULT_WS_PATH="/ws"                            #默认ws路径
DEFAULT_UUID=$(cat /proc/sys/kernel/random/uuid) #默认随机UUID

# 获取并按数字顺序排序IP（支持不同网段从小到大）
IP_ADDRESSES=($(hostname -I | tr ' ' '\n' | sort -t . -k 1,1n -k 2,2n -k 3,3n -k 4,4n | tr '\n' ' '))

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
ExecStart=/usr/local/bin/xrayL -c /etc/xrayL/config.toml
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

# 生成单一类型配置的函数（修复TOML格式）
generate_config() {
	local config_type=$1
	local start_port=$2
	local extra_args=("${@:3}")
	local config_content=""

	for ((i = 0; i < ${#IP_ADDRESSES[@]}; i++)); do
		local current_port=$((start_port + i))
		local tag="tag_${config_type}_$((i + 1))"

		# 生成inbound配置
		config_content+="[[inbounds]]\n"
		config_content+="port = $current_port\n"
		config_content+="protocol = \"$config_type\"\n"
		config_content+="tag = \"$tag\"\n"
		config_content+="[inbounds.settings]\n"

		if [ "$config_type" == "socks" ]; then
			local username=${extra_args[0]}
			local password=${extra_args[1]}
			config_content+="auth = \"password\"\n"
			config_content+="udp = true\n"
			config_content+="ip = \"${IP_ADDRESSES[i]}\"\n"
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
			config_content+="path = \"$ws_path\"\n"  # 减少多余空行，避免格式问题
		fi

		# 生成outbound配置
		config_content+="[[outbounds]]\n"
		config_content+="sendThrough = \"${IP_ADDRESSES[i]}\"\n"
		config_content+="protocol = \"freedom\"\n"
		config_content+="tag = \"$tag\"\n"

		# 生成路由规则（仅添加规则条目，不重复定义[routing]）
		config_content+="[[routing.rules]]\n"
		config_content+="type = \"field\"\n"
		config_content+="inboundTag = \"$tag\"\n"
		config_content+="outboundTag = \"$tag\"\n\n"
	done

	echo -e "$config_content"
}

config_xray() {
	config_type=$1
	mkdir -p /etc/xrayL
	local final_config=""

	# 先添加TOML必需的顶层配置（修复核心问题）
	final_config+="[log]\n"
	final_config+="loglevel = \"warning\"\n\n"  # 添加日志配置，避免空配置警告
	final_config+="[routing]\n"  # 路由顶层配置，所有rules必须在此之下

	if [ "$config_type" == "socks+vmess" ]; then
		# 处理socks配置
		read -p "SOCKS 起始端口 (默认 $DEFAULT_SOCKS_START_PORT): " SOCKS_START_PORT
		SOCKS_START_PORT=${SOCKS_START_PORT:-$DEFAULT_SOCKS_START_PORT}
		read -p "SOCKS 账号 (默认 $DEFAULT_SOCKS_USERNAME): " SOCKS_USERNAME
		SOCKS_USERNAME=${SOCKS_USERNAME:-$DEFAULT_SOCKS_USERNAME}
		read -p "SOCKS 密码 (默认 $DEFAULT_SOCKS_PASSWORD): " SOCKS_PASSWORD
		SOCKS_PASSWORD=${SOCKS_PASSWORD:-$DEFAULT_SOCKS_PASSWORD}

		# 处理vmess配置
		read -p "VMESS 起始端口 (默认 $DEFAULT_VMESS_START_PORT): " VMESS_START_PORT
		VMESS_START_PORT=${VMESS_START_PORT:-$DEFAULT_VMESS_START_PORT}
		read -p "UUID (默认随机): " UUID
		UUID=${UUID:-$DEFAULT_UUID}
		read -p "WebSocket 路径 (默认 $DEFAULT_WS_PATH): " WS_PATH
		WS_PATH=${WS_PATH:-$DEFAULT_WS_PATH}

		# 生成并合并配置（先socks后vmess）
		final_config+=$(generate_config "socks" $SOCKS_START_PORT "$SOCKS_USERNAME" "$SOCKS_PASSWORD")
		final_config+=$(generate_config "vmess" $VMESS_START_PORT "$UUID" "$WS_PATH")

		# 输出socks结果
		echo ""
		echo "生成 SOCKS 配置完成"
		echo "SOCKS 起始端口: $SOCKS_START_PORT"
		echo "SOCKS 结束端口: $((SOCKS_START_PORT + ${#IP_ADDRESSES[@]} - 1))"
		echo "SOCKS 账号: $SOCKS_USERNAME"
		echo "SOCKS 密码: $SOCKS_PASSWORD"

		# 输出vmess结果
		echo ""
		echo "生成 VMESS 配置完成"
		echo "VMESS 起始端口: $VMESS_START_PORT"
		echo "VMESS 结束端口: $((VMESS_START_PORT + ${#IP_ADDRESSES[@]} - 1))"
		echo "UUID: $UUID"
		echo "WS 路径: $WS_PATH"

	elif [ "$config_type" == "socks" ]; then
		read -p "起始端口 (默认 $DEFAULT_SOCKS_START_PORT): " START_PORT
		START_PORT=${START_PORT:-$DEFAULT_SOCKS_START_PORT}
		read -p "SOCKS 账号 (默认 $DEFAULT_SOCKS_USERNAME): " SOCKS_USERNAME
		SOCKS_USERNAME=${SOCKS_USERNAME:-$DEFAULT_SOCKS_USERNAME}
		read -p "SOCKS 密码 (默认 $DEFAULT_SOCKS_PASSWORD): " SOCKS_PASSWORD
		SOCKS_PASSWORD=${SOCKS_PASSWORD:-$DEFAULT_SOCKS_PASSWORD}

		final_config+=$(generate_config "socks" $START_PORT "$SOCKS_USERNAME" "$SOCKS_PASSWORD")

		echo ""
		echo "生成 SOCKS 配置完成"
		echo "起始端口: $START_PORT"
		echo "结束端口: $((START_PORT + ${#IP_ADDRESSES[@]} - 1))"
		echo "SOCKS 账号: $SOCKS_USERNAME"
		echo "SOCKS 密码: $SOCKS_PASSWORD"

	elif [ "$config_type" == "vmess" ]; then
		read -p "起始端口 (默认 $DEFAULT_VMESS_START_PORT): " START_PORT
		START_PORT=${START_PORT:-$DEFAULT_VMESS_START_PORT}
		read -p "UUID (默认随机): " UUID
		UUID=${UUID:-$DEFAULT_UUID}
		read -p "WebSocket 路径 (默认 $DEFAULT_WS_PATH): " WS_PATH
		WS_PATH=${WS_PATH:-$DEFAULT_WS_PATH}

		final_config+=$(generate_config "vmess" $START_PORT "$UUID" "$WS_PATH")

		echo ""
		echo "生成 VMESS 配置完成"
		echo "起始端口: $START_PORT"
		echo "结束端口: $((START_PORT + ${#IP_ADDRESSES[@]} - 1))"
		echo "UUID: $UUID"
		echo "WS 路径: $WS_PATH"

	else
		echo "类型错误！仅支持socks、vmess和socks+vmess."
		exit 1
	fi

	# 写入最终配置并重启服务
	echo -e "$final_config" >/etc/xrayL/config.toml
	systemctl restart xrayL.service
	systemctl --no-pager status xrayL.service
	echo ""
}

main() {
	[ -x "$(command -v xrayL)" ] || install_xray
	if [ $# -eq 1 ]; then
		config_type="$1"
	else
		read -p "选择生成的节点类型 (socks/vmess/socks+vmess): " config_type
	fi
	config_xray "$config_type"
}

main "$@"

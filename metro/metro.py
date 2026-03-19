import networkx as nx
import matplotlib.pyplot as plt
import base64
from io import BytesIO

# 设置中文字体，防止 matplotlib 中文乱码 (Windows 特供)
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def run_resilience_test(station: str, crowd_flow: float, weather: str, show_plot: bool = False) -> dict:
    # 1. 建立微型地铁网
    G = nx.Graph()
    edges = [('A站', 'B站'), ('B站', 'C站'), ('C站', 'D站'), ('B站', 'E站'), ('E站', 'F站')]
    G.add_edges_from(edges)
    
    initial_efficiency = nx.global_efficiency(G)
    
    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1)
    
    weather_map = {"sunny": "晴天", "heavy_rain": "大雨", "typhoon": "台风"}
    weather_desc = weather_map.get(weather, weather)
    
    plt.title(f"正常运行 (天气:{weather_desc}, 人流:{crowd_flow}万)\n初始效率: {initial_efficiency:.2f}")
    nx.draw(G, with_labels=True, node_color='lightblue', node_size=800, font_weight='bold')

    # 2. 模拟蓄意攻击或事故关闭
    target_node = station
    if target_node not in G.nodes:
        # 如果输入的站点不在图里，默认选度中心性最高的
        centrality = nx.degree_centrality(G)
        target_node = max(centrality, key=centrality.get)
        msg = f"未找到指定站，系统自动接管：关闭枢纽 {target_node} 站。"
    else:
        msg = f"突发事件：{target_node} 发生严重故障，已紧急关闭该站。"
        
    G.remove_node(target_node)
    
    # 3. 评估攻击后效率
    new_efficiency = nx.global_efficiency(G)
    
    # 根据天气和人流量对效率进一步施加惩罚系数
    penalty = 0.0
    if weather == "heavy_rain":
        penalty += 0.05
    elif weather == "typhoon":
        penalty += 0.15
        
    if crowd_flow > 10:
        penalty += 0.1
    elif crowd_flow > 5:
        penalty += 0.05
        
    final_efficiency = max(0.0, new_efficiency - penalty)

    components = list(nx.connected_components(G))
    largest_component = max(components, key=len) if components else []
    
    report_text = f"{msg}<br>网络断裂成了 {len(components)} 个互不相通的独立区间。<br>最大贯通子网余留站点数: {len(largest_component)}。<br>受天气及客流影响，最终全局效率大幅降至: <b>{final_efficiency:.4f}</b> (原: {initial_efficiency:.4f})"

    # 画出被攻击后的网络图
    plt.subplot(1, 2, 2)
    plt.title(f"故障后 ({target_node} 瘫痪)\n当前效率: {final_efficiency:.2f}")
    nx.draw(G, with_labels=True, node_color='lightcoral', node_size=800, font_weight='bold') 
    
    # 将图像输出为 base64 传给前端
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode('utf-8')
    
    if show_plot:
        plt.show()  # 手动测试时弹出窗口
        
    plt.close()
    
    return {
        "report": report_text,
        "image_b64": img_b64
    }

if __name__ == "__main__":
    print("=== 本机验证模式 ===")
    # 您可以在这里随意修改参数查看结果
    test_station = "A站"
    test_crowd_flow = 8.0
    test_weather = "typhoon"
    
    print(f"正在测试 -> 站点: {test_station}, 人流: {test_crowd_flow}万, 天气: {test_weather}")
    
    # 传入 show_plot=True 即可看到 python 的 matplotlib 弹窗
    result = run_resilience_test(test_station, test_crowd_flow, test_weather, show_plot=True)
    
    # 打印给终端看的文字报告
    text_only_report = result["report"].replace("<br>", "\n").replace("<b>", "").replace("</b>", "")
    print("\n【研判报告】")
    print(text_only_report)

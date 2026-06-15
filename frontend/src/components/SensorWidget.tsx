import React from 'react';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts';
interface SensorWidgetProps {
    title: string;
    unit: string;
    currentValue: number;
    history: number[];
    min: number;
    max: number;
    color?: string;
    icon?: React.ReactNode;
}

export const SensorWidget: React.FC<SensorWidgetProps> = ({
    title,
    unit,
    currentValue,
    history,
    min,
    max,
    color = '#00F0FF', // Sarak Primary
    icon
}) => {
    // Calcula a porcentagem do gauge
    const percentage = Math.min(Math.max((currentValue - min) / (max - min), 0), 1);
    
    // Cor condicional simples baseada no threshold (> 80% do range max)
    const activeColor = percentage > 0.8 ? '#EF4444' : percentage > 0.6 ? '#F97316' : color;

    const chartOption: echarts.EChartsOption = {
        grid: {
            left: 0,
            right: 0,
            bottom: 0,
            top: '65%', // Empurra a linha para a parte inferior para não cruzar o valor central
            containLabel: false
        },
        xAxis: {
            type: 'category',
            show: false,
            data: history.map((_, i) => i)
        },
        yAxis: {
            type: 'value',
            show: false,
            min: 'dataMin', // Ajusta o Y baseado nos dados
            max: 'dataMax'
        },
        series: [
            // GAUGE ARC
            {
                type: 'gauge',
                startAngle: 180,
                endAngle: 0,
                center: ['50%', '50%'],
                radius: '100%',
                min: min,
                max: max,
                splitNumber: 1,
                axisLine: {
                    lineStyle: {
                        width: 8,
                        color: [[1, 'rgba(255, 255, 255, 0.05)']]
                    }
                },
                progress: {
                    show: true,
                    width: 8,
                    itemStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                            { offset: 0, color: activeColor + '40' },
                            { offset: 1, color: activeColor }
                        ])
                    }
                },
                pointer: { show: false },
                axisTick: { show: false },
                splitLine: { show: false },
                axisLabel: { show: false },
                detail: { show: false },
                data: [{ value: currentValue }]
            },
            // SPARKLINE AREA
            {
                type: 'line',
                data: history,
                smooth: true,
                showSymbol: false,
                lineStyle: {
                    width: 2,
                    color: activeColor
                },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: activeColor + '40' },
                        { offset: 1, color: activeColor + '00' }
                    ])
                }
            }
        ]
    };

    return (
        <div className="relative bg-theme-card border-theme rounded-theme p-4 shadow-2xl flex flex-col items-center justify-center overflow-hidden h-[300px] group hover:border-[var(--theme-primary)]/50 transition-colors">
            
            {/* Título e Ícone */}
            <div className="absolute top-4 left-4 right-4 flex justify-between items-center z-10">
                <span className="text-[10px] font-black text-white/40 uppercase tracking-widest">{title}</span>
                {icon && <div className="text-white/20 group-hover:text-[var(--theme-primary)] transition-colors">{icon}</div>}
            </div>

            {/* Valor Central Overlay */}
            <div className="absolute inset-0 flex flex-col items-center justify-center z-10 pointer-events-none mt-2">
                <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-black text-white tracking-tighter" style={{ color: activeColor }}>
                        {currentValue.toFixed(1)}
                    </span>
                    <span className="text-[10px] font-bold text-white/40 uppercase">{unit}</span>
                </div>
            </div>

            {/* ECharts Instance */}
            <div className="w-full h-full pt-6">
                <ReactECharts 
                    option={chartOption} 
                    style={{ height: '100%', width: '100%' }}
                />
            </div>
            
            {/* Overlay Gradient for depth */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent pointer-events-none z-0" />
        </div>
    );
};

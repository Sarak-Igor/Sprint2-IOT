import React from 'react';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts';

interface MiniSensorWidgetProps {
    title: string;
    unit: string;
    currentValue: number;
    history: number[];
    min: number;
    max: number;
    thresholds?: {
        warning?: number;
        critical?: number;
    };
    color?: string;
}

export const MiniSensorWidget: React.FC<MiniSensorWidgetProps> = ({
    title,
    unit,
    currentValue,
    history,
    min,
    max,
    thresholds,
    color = '#00F0FF'
}) => {
    const isCritical = thresholds?.critical && currentValue >= thresholds.critical;
    const isWarning = thresholds?.warning && currentValue >= thresholds.warning;
    
    const activeColor = isCritical ? '#F43F5E' : isWarning ? '#FBBF24' : color;

    const chartOption: echarts.EChartsOption = {
        grid: {
            left: 0,
            right: 0,
            bottom: 0,
            top: 0,
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
            min: 'dataMin',
            max: 'dataMax'
        },
        series: [
            // GAUGE ARC (Mini)
            {
                type: 'gauge',
                startAngle: 180,
                endAngle: 0,
                center: ['50%', '85%'],
                radius: '140%',
                min: min,
                max: max,
                splitNumber: 1,
                axisLine: {
                    lineStyle: {
                        width: 3,
                        color: [[1, 'rgba(255, 255, 255, 0.03)']]
                    }
                },
                progress: {
                    show: true,
                    width: 3,
                    itemStyle: {
                        color: activeColor
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
        <div className="bg-black/20 border border-white/5 rounded-2xl p-3 flex flex-col gap-2 hover:border-white/10 transition-all group overflow-hidden">
            <div className="flex justify-between items-start">
                <span className="text-[8px] font-black text-white/30 uppercase tracking-widest truncate max-w-[60%]">
                    {title}
                </span>
                <div className="flex items-baseline gap-0.5">
                    <span className="text-sm font-black tracking-tighter" style={{ color: activeColor }}>
                        {currentValue.toFixed(1)}
                    </span>
                    <span className="text-[7px] font-bold text-white/20 uppercase">{unit}</span>
                </div>
            </div>
            
            <div className="h-10 w-full opacity-60 group-hover:opacity-100 transition-opacity">
                <ReactECharts 
                    option={chartOption} 
                    style={{ height: '100%', width: '100%' }}
                    lazyUpdate={true}
                />
            </div>
        </div>
    );
};

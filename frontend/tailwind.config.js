/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Solvely 配色体系
        solvely: {
          primary: '#4285F4',      // 主色：天蓝色
          secondary: '#F5F7FA',    // 辅色：浅灰色
          white: '#FFFFFF',        // 纯白色
          text: {
            dark: '#333333',       // 深灰色文字
            light: '#666666',      // 浅灰色文字
          },
          warning: {
            bg: '#FFF8E1',         // 警告背景
          },
          error: '#DC3545',        // 错误红色
          success: '#28A745',      // 成功绿色
        }
      },
      borderRadius: {
        // Solvely 圆角尺寸
        'solvely-sm': '6px',
        'solvely': '8px',
        'solvely-lg': '12px',
      },
      fontSize: {
        // Solvely 字体尺寸
        'solvely-base': '16px',
        'solvely-lg': '18px',
        'solvely-xl': '32px',
      },
      spacing: {
        // Solvely 间距
        '18': '4.5rem',   // 72px
      },
      boxShadow: {
        // Solvely 阴影
        'solvely': '0 2px 12px rgba(0, 0, 0, 0.08)',
        'solvely-lg': '0 4px 12px rgba(66, 133, 244, 0.3)',
      },
      background: {
        'solvely-gradient': 'linear-gradient(135deg, #4285F4, #5BA3F5)',
      }
    },
  },
  plugins: [],
}

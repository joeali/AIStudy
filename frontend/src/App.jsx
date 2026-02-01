import React, { useState, useEffect, useRef } from 'react';
import { BookOpen, Brain, AlertCircle, Target, TrendingUp, Award, Plus, X, BarChart3, Sparkles, Check, Clock, RefreshCw, Image, Upload, FileText } from 'lucide-react';

// API 配置
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// 唯一ID生成器
let messageIdCounter = 0;
const generateMessageId = () => `msg_${Date.now()}_${messageIdCounter++}`;

export default function AIStudyCompanion() {
  const [activeTab, setActiveTab] = useState('solve');
  const [question, setQuestion] = useState('');
  const [conversation, setConversation] = useState([]);
  const [isThinking, setIsThinking] = useState(false);
  const [mistakes, setMistakes] = useState([]);
  const [learningData, setLearningData] = useState(null);
  const [showAddMistake, setShowAddMistake] = useState(false);
  const [uploadedImage, setUploadedImage] = useState(null);
  const [quizParams, setQuizParams] = useState({
    subject: '数学',
    difficulty: '中等',
    count: 5
  });

  // 历史记录相关状态
  const [showHistory, setShowHistory] = useState(false);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [analysisHistory, setAnalysisHistory] = useState([]); // 错题分析历史
  const [historyTab, setHistoryTab] = useState('conversation'); // 历史记录对话框标签

  // 错题标记相关状态
  const [markingMode, setMarkingMode] = useState(false);
  const [markedErrors, setMarkedErrors] = useState([]);
  const [isDrawing, setIsDrawing] = useState(false);
  const [boxes, setBoxes] = useState([]);
  const [currentBox, setCurrentBox] = useState(null);
  const [startPoint, setStartPoint] = useState(null);
  const [imageContainerRef, setImageContainerRef] = useState(null);

  // 图片弹窗相关状态
  const [showImageModal, setShowImageModal] = useState(false);
  const [modalImage, setModalImage] = useState(null);

  // Toast通知状态
  const [toast, setToast] = useState(null);

  // File input refs
  const fileInputRef = useRef(null);
  const mistakeFileInputRef = useRef(null);

  // 显示Toast通知
  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  // 从 localStorage 加载历史记录
  useEffect(() => {
    const saved = localStorage.getItem('conversationHistory');
    if (saved) {
      try {
        setConversationHistory(JSON.parse(saved));
      } catch (e) {
        console.error('加载历史记录失败:', e);
      }
    }

    // 加载错题分析历史
    const savedAnalysis = localStorage.getItem('analysisHistory');
    if (savedAnalysis) {
      try {
        setAnalysisHistory(JSON.parse(savedAnalysis));
      } catch (e) {
        console.error('加载分析历史失败:', e);
      }
    }
  }, []);

  // 调试：监听对话状态变化
  useEffect(() => {
    if (conversation.length > 0) {
      const lastMsg = conversation[conversation.length - 1];
      console.log('[React渲染] 对话状态更新:', {
        长度: conversation.length,
        最后一条消息: {
          id: lastMsg.id,
          role: lastMsg.role,
          showAnalyzing: lastMsg.showAnalyzing,
          content: lastMsg.content,
          content长度: lastMsg.content?.length || 0
        }
      });
    }
  }, [conversation]);

  // 保存当前对话到历史记录
  const saveToHistory = () => {
    if (conversation.length === 0) return;

    const historyItem = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      preview: conversation[0]?.content?.substring(0, 50) + '...' || '新对话',
      conversation: conversation,
      question: question,
      hasImage: uploadedImage !== null
    };

    const newHistory = [historyItem, ...conversationHistory].slice(0, 20); // 只保留最近20条
    setConversationHistory(newHistory);
    localStorage.setItem('conversationHistory', JSON.stringify(newHistory));
  };

  // 保存错题分析到历史记录
  const saveAnalysisToHistory = (mistakes, analysisContent, image) => {
    const analysisItem = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      mistakes: mistakes,
      analysis: analysisContent,
      image: image,
      mistakeCount: mistakes.length,
      preview: `检测到 ${mistakes.length} 道错题 - ${new Date().toLocaleDateString('zh-CN')}`
    };

    const newHistory = [analysisItem, ...analysisHistory].slice(0, 50); // 保留最近50条
    setAnalysisHistory(newHistory);
    localStorage.setItem('analysisHistory', JSON.stringify(newHistory));
  };

  // 诊断和引导相关状态
  const [isGuidanceMode, setIsGuidanceMode] = useState(false);
  const [currentDiagnosis, setCurrentDiagnosis] = useState(null);
  const [guidanceConversation, setGuidanceConversation] = useState([]);

  // 找错题功能状态
  const [detectedMistakes, setDetectedMistakes] = useState([]);
  const [currentGuidingMistake, setCurrentGuidingMistake] = useState(null);  // 当前正在引导的错题

  // 从真实数据生成学习报告
  useEffect(() => {
    const generateLearningData = () => {
      if (analysisHistory.length === 0) {
        // 没有历史数据时，使用默认空数据
        return {
          weeklyHours: 0,
          questionsCompleted: 0,
          accuracy: 0,
          weekSummary: {
            overview: '还没有学习记录。上传试卷进行错题分析后，这里会显示您的学习情况。',
            changes: [
              { type: 'info', text: '开始第一次错题分析吧！' }
            ],
            studyHabits: null
          },
          subjectAnalysis: [],
          totalEstimatedImprovement: 0
        };
      }

      // 统计真实数据
      const totalAnalyses = analysisHistory.length;
      const totalMistakes = analysisHistory.reduce((sum, item) => sum + item.mistakeCount, 0);

      // 获取最近的分析
      const recentAnalyses = analysisHistory.slice(0, 5);
      const recentAnalysisText = recentAnalyses.map(item => item.analysis).join('\n\n');

      // 计算时间跨度
      const now = new Date();
      const firstAnalysis = new Date(analysisHistory[analysisHistory.length - 1].timestamp);
      const daysDiff = Math.max(1, Math.ceil((now - firstAnalysis) / (1000 * 60 * 60 * 24)));

      // 生成概述
      const overview = `已完成 ${totalAnalyses} 次错题分析，累计检测到 ${totalMistakes} 道错题。学习周期 ${daysDiff} 天。${recentAnalyses.length > 0 ? '系统已为您生成详细的学情分析报告。' : ''}`;

      // 生成变化列表（从最近的学情分析中提取）
      const changes = [];
      recentAnalyses.forEach((item, idx) => {
        if (item.mistakeCount > 0) {
          changes.push({
            type: 'info',
            text: `${new Date(item.timestamp).toLocaleDateString('zh-CN')} 检测到 ${item.mistakeCount} 道错题`
          });
        }
      });

      // 提取学科分析（基于错题分布）
      const subjectMap = {};
      analysisHistory.forEach(item => {
        item.mistakes.forEach(mistake => {
          const subject = '综合'; // 可以从题号或分析中推断学科
          if (!subjectMap[subject]) {
            subjectMap[subject] = {
              name: subject,
              accuracy: Math.max(40, 100 - (totalMistakes * 2)),
              change: 0,
              weakPoints: [],
              improvementPlan: {
                targetPoints: Math.min(30, totalMistakes * 3),
                weeks: 4,
                actions: [
                  '复习错题，总结解题方法',
                  '加强基础知识点练习',
                  '定期进行错题重做'
                ]
              }
            };
          }
        });
      });

      // 使用最近的学情分析内容作为薄弱点
      if (recentAnalyses.length > 0 && recentAnalyses[0].analysis) {
        const latestAnalysis = recentAnalyses[0].analysis;
        // 从学情分析中提取关键信息
        if (latestAnalysis.includes('学习优势') || latestAnalysis.includes('薄弱')) {
          changes.push({
            type: 'positive',
            text: '已完成学情分析，发现学习优势和薄弱环节'
          });
        }
      }

      return {
        weeklyHours: parseFloat((totalAnalyses * 0.5).toFixed(1)), // 每次分析约0.5小时
        questionsCompleted: totalMistakes * 3, // 假设每道错题对应3题练习
        accuracy: Math.max(50, 85 - totalMistakes * 2),
        weekSummary: {
          overview,
          changes: changes.length > 0 ? changes.slice(0, 5) : [{ type: 'info', text: '继续加油！' }],
          studyHabits: {
            peakTime: '根据学习记录统计',
            avgSessionLength: '约30分钟/次',
            consistency: totalAnalyses > 3 ? '保持良好' : '建议增加频率'
          }
        },
        subjectAnalysis: Object.values(subjectMap),
        totalEstimatedImprovement: Math.min(50, totalMistakes * 5)
      };
    };

    const realData = generateLearningData();
    setLearningData(realData);
  }, [analysisHistory]); // 依赖 analysisHistory，当它变化时重新计算

  // ==================== API 调用函数 ====================

  // 简化状态管理（后端会自动排队）
  const [pendingRequests, setPendingRequests] = useState(0);

  // 调用后端聊天 API（支持流式输出）
  const handleSolveQuestion = async () => {
    // 防止空请求
    if (!question.trim() && !uploadedImage) return;

    // 检查是否是确认错题的回复
    if (detectedMistakes.length > 0 && !isGuidanceMode) {
      const trimmedQuestion = question.trim().toLowerCase();

      // 检查是否是确认回复
      if (trimmedQuestion === '全部' || /^\d[,，\s\d]+$/.test(trimmedQuestion)) {
        let selectedMistakes = [];

        if (trimmedQuestion === '全部') {
          selectedMistakes = [...detectedMistakes];
        } else {
          // 解析题号
          const numbers = trimmedQuestion.split(/[,，\s]+/).map(n => parseInt(n.trim())).filter(n => !isNaN(n));
          selectedMistakes = detectedMistakes.filter((_, idx) => numbers.includes(idx + 1));
        }

        if (selectedMistakes.length > 0) {
          // 开始对选中的错题进行逐一引导
          setQuestion('');
          // startGuidanceForMistakes 会管理自己的 isThinking 状态
          await startGuidanceForMistakes(selectedMistakes);
          return;
        }
      } else if (trimmedQuestion === '重新检测') {
        // 清空对话，准备重新检测
        setDetectedMistakes([]);
        setConversation([]);
        setQuestion('请上传试卷图片进行检测');
        return;
      }
    }

    // 如果在引导模式，使用引导API
    if (isGuidanceMode) {
      setQuestion('');
      // continueGuidance 会管理自己的 isThinking 状态
      await continueGuidance(question);
      return;
    }

    console.log('🚀 发送请求（后端会自动排队）...');
    setPendingRequests(prev => prev + 1);
    setIsThinking(true);

    // 检查对话中最后一条是否是刚上传的图片消息（有image但content为空）
    const lastMessage = conversation[conversation.length - 1];
    const isLastMessageImageOnly = lastMessage &&
                                   lastMessage.role === 'user' &&
                                   lastMessage.image &&
                                   !lastMessage.content.trim();

    let userMessage;
    let currentImage = uploadedImage;

    if (isLastMessageImageOnly && !question.trim()) {
      // 如果最后一条是图片消息且没有输入文字，更新这条消息的content
      const currentMarks = [...markedErrors];
      const content = markedErrors.length > 0
        ? `我已标记了${markedErrors.length}道错题，请为我生成详细的学情分析。`
        : '请分析这张试卷';

      userMessage = {
        ...lastMessage,
        content: content
      };
      currentImage = lastMessage.image; // 使用已有的图片

      // 更新对话中的消息
      setConversation(prev => {
        const newConversation = [...prev];
        newConversation[newConversation.length - 1] = userMessage;
        return newConversation;
      });

      // 清空标记
      setMarkedErrors([]);
      setUploadedImage(null);

      // 执行错题检测（detectMistakes 会管理自己的 isThinking 状态）
      setPendingRequests(prev => prev - 1);
      setIsThinking(false);
      await detectMistakes(currentImage, currentMarks);
      return;
    } else {
      // 否则创建新消息
      userMessage = {
        role: 'user',
        content: question || '请分析这道题目',
        image: uploadedImage
      };
      currentImage = uploadedImage;

      // 清空输入
      setQuestion('');
      setUploadedImage(null);

      // 添加用户消息到对话
      setConversation(prev => [...prev, userMessage]);
    }

    console.log('[前端] 创建AI消息，设置showAnalyzing=true');

    // 创建一个空的助手消息，用于流式更新
    // 同时标记为正在分析状态
    const assistantMessageId = generateMessageId();
    const assistantMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      showAnalyzing: true  // 控制是否显示加载动画
    };

    // 使用函数式更新确保状态立即生效
    setConversation(prev => {
      const newConversation = [...prev, assistantMessage];
      console.log('[前端] 添加消息到对话，消息ID:', assistantMessageId);
      console.log('[前端] 新对话长度:', newConversation.length);
      console.log('[前端] 消息状态:', assistantMessage);
      return newConversation;
    });

    try {
      // 使用流式API
      const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage.content,
          conversation_history: conversation,
          image_data: currentImage?.data
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // 读取流式响应
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // 处理SSE格式的数据
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || ''; // 保留未完整的数据块

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            console.log('[前端 SSE] 收到数据:', line.substring(0, 100));
            try {
              const data = JSON.parse(line.slice(6));

              if (data.error) {
                // 错误处理
                setConversation(prev => prev.map(msg =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: `抱歉，${data.error}`, showAnalyzing: false }
                    : msg
                ));
                // finally 块会处理状态重置
                return;
              }

              // 处理状态消息 - 更新UI状态
              if (data.status) {
                console.log('[前端 SSE] 收到状态消息:', data.status, data.message);
                // 状态消息只是确认，不需要改变showAnalyzing（初始已经是true）
                // 收到状态消息说明后端已开始处理
                continue;
              }

              if (data.content) {
                // 逐字更新内容，移除加载状态
                setConversation(prev => {
                  const updated = prev.map(msg =>
                    msg.id === assistantMessageId
                      ? {
                          ...msg,
                          content: msg.content + data.content,
                          showAnalyzing: false  // 开始有内容后，移除加载状态
                        }
                      : msg
                  );
                  const targetMsg = updated.find(m => m.id === assistantMessageId);
                  console.log('[前端 SSE] 收到内容:', data.content, '新长度:', targetMsg?.content?.length || 0);
                  return updated;
                });
              }

              if (data.done) {
                // 流式传输完成，finally 块会处理状态重置
                console.log('[前端] 收到完成信号');
              }

            } catch (e) {
              console.error('解析SSE数据失败:', e);
            }
          }
        }
      }

      // 保存到历史记录
      setTimeout(() => saveToHistory(), 100);

    } catch (error) {
      console.error('❌ 请求失败:', error);
      setConversation(prev => prev.map(msg =>
        msg.id === assistantMessageId
          ? { ...msg, content: `抱歉，遇到了一些问题：${error.message}。请稍后重试或检查后端服务。` }
          : msg
      ));
    } finally {
      setIsThinking(false);
      setPendingRequests(prev => Math.max(0, prev - 1));
      console.log('✅ 请求完成');
    }
  };

  // 分离的添加错题函数（独立调用，不阻塞主流程）
  const addMistakeToNotebook = async (image) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/analyze/question`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_data: image.data,
          image_type: image.type
        })
      });

      if (!response.ok) {
        console.error('分析失败');
        return;
      }

      const data = await response.json();

      if (data.success && data.data) {
        const newMistake = {
          id: Date.now(),
          question: data.data.question || '未知题目',
          subject: data.data.subject || '未知',
          topic: data.data.topic || '',
          difficulty: data.data.difficulty || '中等',
          correctAnswer: data.data.correctAnswer || '',
          errorReason: data.data.errorReason || '',
          yourAnswer: data.data.yourAnswer || '已在对话中讨论',
          addedAt: new Date().toISOString(),
          image: image,
          reviewed: false,
          autoAdded: true,
          reviewHistory: []
        };

        setMistakes(prev => [newMistake, ...prev]);

        setConversation(prev => [...prev, {
          role: 'assistant',
          content: '✅ 检测到错题，已自动添加到错题本！'
        }]);
      }
    } catch (error) {
      console.error('Error extracting mistake:', error);
    }
  };

  // 处理图片上传
  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      // 检查文件大小(限制10MB)
      if (file.size > 10 * 1024 * 1024) {
        showToast('图片文件过大,请上传小于10MB的图片', 'error');
        e.target.value = ''; // 清空input
        return;
      }

      // 检查文件类型
      if (!file.type.startsWith('image/')) {
        showToast('请上传图片文件', 'error');
        e.target.value = ''; // 清空input
        return;
      }

      const reader = new FileReader();
      reader.onload = (event) => {
        const base64Data = event.target.result.split(',')[1];
        const mediaType = file.type;

        // 创建图片对象
        const imageData = {
          data: base64Data,
          type: mediaType,
          preview: event.target.result
        };

        // 直接添加到对话中，而不是保存到 uploadedImage
        const imageMessage = {
          role: 'user',
          content: '', // 空内容，不显示文字
          image: imageData
        };

        setConversation(prev => [...prev, imageMessage]);

        // 同时保存到 uploadedImage 供后续使用（但不显示在中间）
        setUploadedImage(imageData);

        // 清空input
        e.target.value = '';
      };
      reader.onerror = () => {
        showToast('图片读取失败,请重试', 'error');
        e.target.value = ''; // 清空input
      };
      reader.readAsDataURL(file);
    }
  };

  const removeImage = () => {
    setUploadedImage(null);
  };

  // ==================== 诊断和引导功能 ====================

  // 开始诊断流程
  const startDiagnosis = async (questionText, studentAnswer, image) => {
    setIsThinking(true);

    // 创建消息ID用于流式更新
    const assistantMessageId = Date.now();
    const assistantMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '🔍 正在分析错误原因...'
    };
    setConversation(prev => [...prev, assistantMessage]);

    try {
      const response = await fetch(`${API_BASE_URL}/api/diagnose/analyze/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: questionText,
          student_answer: studentAnswer || '不会做/做错了',
          image_data: image?.data
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // 读取流式响应
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let streamedContent = '';
      let finalData = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // 处理SSE格式的数据
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              // 错误处理
              if (data.error) {
                setConversation(prev => prev.map(msg =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: `抱歉，${data.error}` }
                    : msg
                ));
                return;
              }

              // 状态更新
              if (data.status === 'analyzing') {
                setConversation(prev => prev.map(msg =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: data.message || '' }
                    : msg
                ));
              }

              // 内容更新
              if (data.content) {
                streamedContent += data.content;
                setConversation(prev => prev.map(msg =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: streamedContent }
                    : msg
                ));
              }

              // 完成并获取最终数据
              if (data.done && data.data) {
                finalData = data.data;
              }

            } catch (e) {
              console.error('解析SSE数据失败:', e);
            }
          }
        }
      }

      if (finalData) {
        setCurrentDiagnosis(finalData);

        // 显示诊断结果
        setConversation(prev => prev.map(msg =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: `📋 **诊断结果**

**知识点**: ${finalData.knowledge_point}
**错误类型**: ${finalData.error_type}

**问题分析**: ${finalData.problem_description}

---`,
                isDiagnosis: true
              }
            : msg
        ));

        // 自动开始引导
        setTimeout(() => startGuidance(questionText, finalData), 500);
      }

    } catch (error) {
      console.error('诊断失败:', error);
      setConversation(prev => prev.map(msg =>
        msg.id === assistantMessageId
          ? { ...msg, content: '抱歉，诊断过程出现问题，请稍后重试。' }
          : msg
      ));
    } finally {
      setIsThinking(false);
    }
  };

  // 对选中的错题逐一进行苏格拉底式引导
  const startGuidanceForMistakes = async (mistakes) => {
    if (mistakes.length === 0) return;

    setIsThinking(true);
    setIsGuidanceMode(true);
    setCurrentGuidingMistake(mistakes[0]);

    try {
      // 显示开始引导的消息
      setConversation(prev => [...prev, {
        role: 'assistant',
        content: `📚 **开始错题引导**

我将引导你逐一分析以下 ${mistakes.length} 道错题：

${mistakes.map((m, idx) => `${idx + 1}. 第${m.question_no || '?'}题`).join('\n')}

💡 **引导方式**：我不会直接给你答案，而是通过提问引导你自己思考。

---

👨‍🏫 **第一道题：第${mistakes[0].question_no || '?'}题**

现在，请告诉我这道题的内容，或者直接上传题目图片，我会引导你一步步解答。

(输入"下一题"可跳过当前题目)`,
        isGuidance: true
      }]);
    } catch (error) {
      console.error('启动引导失败:', error);
      setIsGuidanceMode(false);
      setCurrentGuidingMistake(null);
    } finally {
      setIsThinking(false);
    }
  };

  // 开始苏格拉底式引导
  const startGuidance = async (questionText, diagnosis) => {
    setIsThinking(true);
    setIsGuidanceMode(true);

    // 创建消息ID用于流式更新
    const assistantMessageId = Date.now();
    const assistantMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '🤔 正在思考如何引导...'
    };
    setConversation(prev => [...prev, assistantMessage]);

    try {
      const response = await fetch(`${API_BASE_URL}/api/diagnose/guide/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: questionText,
          diagnosis: `${diagnosis.knowledge_point} - ${diagnosis.problem_description}`,
          student_response: null,
          conversation_history: []
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // 读取流式响应
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let streamedContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // 处理SSE格式的数据
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              // 错误处理
              if (data.error) {
                setConversation(prev => prev.map(msg =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: `抱歉，${data.error}` }
                    : msg
                ));
                return;
              }

              // 状态更新
              if (data.status === 'thinking') {
                setConversation(prev => prev.map(msg =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: data.message || '' }
                    : msg
                ));
              }

              // 内容更新
              if (data.content) {
                streamedContent += data.content;
                setConversation(prev => prev.map(msg =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: streamedContent }
                    : msg
                ));
              }

            } catch (e) {
              console.error('解析SSE数据失败:', e);
            }
          }
        }
      }

      // 更新最终消息
      setConversation(prev => prev.map(msg =>
        msg.id === assistantMessageId
          ? {
              ...msg,
              content: `👨‍🏫 **开始引导**

${streamedContent}

---
💡 请回答老师的问题，我会一步步引导你找到正确答案。
（输入"退出引导"返回普通对话模式）`,
              isGuidance: true
            }
          : msg
      ));

      setGuidanceConversation([{
        role: 'assistant',
        content: streamedContent
      }]);

    } catch (error) {
      console.error('引导启动失败:', error);
      setIsGuidanceMode(false);
      setConversation(prev => prev.map(msg =>
        msg.id === assistantMessageId
          ? { ...msg, content: '抱歉，引导启动失败。' }
          : msg
      ));
    } finally {
      setIsThinking(false);
    }
  };

  // 继续引导对话
  const continueGuidance = async (userMessage) => {
    if (userMessage.includes('退出引导')) {
      setIsGuidanceMode(false);
      setGuidanceConversation([]);
      setCurrentDiagnosis(null);
      setCurrentGuidingMistake(null);
      setConversation(prev => [...prev, {
        role: 'assistant',
        content: '✅ 已退出引导模式，回到普通对话。'
      }]);
      return;
    }

    // 如果在错题引导模式，检查是否要切换到下一题
    if (currentGuidingMistake && (userMessage.includes('下一题') || userMessage.includes('跳过'))) {
      const currentIndex = detectedMistakes.indexOf(currentGuidingMistake);
      const nextMistake = detectedMistakes[currentIndex + 1];

      if (nextMistake) {
        // 切换到下一道题
        setCurrentGuidingMistake(nextMistake);
        setConversation(prev => [...prev, {
          role: 'user',
          content: userMessage
        }, {
          role: 'assistant',
          content: `✅ 已跳过第${currentGuidingMistake.question_no || '?'}题

---

👨‍🏫 **下一道题：第${nextMistake.question_no || '?'}题**

请告诉我这道题的内容，或上传题目图片，我会引导你一步步解答。`,
          isGuidance: true
        }]);
        return;
      } else {
        // 所有错题已完成
        setCurrentGuidingMistake(null);
        setIsGuidanceMode(false);
        setConversation(prev => [...prev, {
          role: 'assistant',
          content: `🎉 恭喜！你已经完成了所有错题的引导学习。

📊 **学习总结**：
- 共学习了 ${detectedMistakes.length} 道错题
- 使用了苏格拉底式引导方法，通过提问启发思考

💡 **建议**：
1. 复习今天学习到的解题方法
2. 对错题进行整理和总结
3. 尝试独立解答类似的题目

继续加油！`,
          isGuidance: true
        }]);
        return;
      }
    }

    setIsThinking(true);

    // 创建消息ID用于流式更新
    const assistantMessageId = Date.now();
    const assistantMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '🤔...'
    };
    setConversation(prev => [...prev, assistantMessage]);

    try {
      const response = await fetch(`${API_BASE_URL}/api/diagnose/guide/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: conversation.find(m => m.image)?.content || '当前题目',
          diagnosis: currentDiagnosis ? `${currentDiagnosis.knowledge_point} - ${currentDiagnosis.problem_description}` : '待诊断',
          student_response: userMessage,
          conversation_history: guidanceConversation
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // 读取流式响应
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let streamedContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // 处理SSE格式的数据
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              // 错误处理
              if (data.error) {
                setConversation(prev => prev.map(msg =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: `抱歉，${data.error}` }
                    : msg
                ));
                return;
              }

              // 状态更新
              if (data.status === 'thinking') {
                setConversation(prev => prev.map(msg =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: data.message || '' }
                    : msg
                ));
              }

              // 内容更新
              if (data.content) {
                streamedContent += data.content;
                setConversation(prev => prev.map(msg =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: streamedContent, isGuidance: true }
                    : msg
                ));
              }

            } catch (e) {
              console.error('解析SSE数据失败:', e);
            }
          }
        }
      }

      // 更新引导对话历史
      const newGuidanceMsg = { role: 'assistant', content: streamedContent };
      setGuidanceConversation(prev => [...prev, { role: 'user', content: userMessage }, newGuidanceMsg]);

    } catch (error) {
      console.error('引导继续失败:', error);
      setConversation(prev => prev.map(msg =>
        msg.id === assistantMessageId
          ? { ...msg, content: '抱歉，引导过程出现问题。', isGuidance: true }
          : msg
      ));
    } finally {
      setIsThinking(false);
    }
  };

  // ==================== 找错题功能 ====================

  // 检测图片中的错题
  const detectMistakes = async (imageToDetect = null, marks = []) => {
    const image = imageToDetect || uploadedImage;

    if (!image) {
      alert('请先上传题目图片');
      return;
    }

    setIsThinking(true);
    setPendingRequests(prev => prev + 1);
    console.log('[detectMistakes] 创建AI消息，设置showAnalyzing=true');

    // 创建助手消息用于流式更新
    const assistantMessageId = generateMessageId();
    const assistantMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      showAnalyzing: true  // 初始显示加载动画
    };
    setConversation(prev => {
      console.log('[detectMistakes] 添加消息到对话，消息ID:', assistantMessageId);
      return [...prev, assistantMessage];
    });

    // 存储流式内容和分析结果
    let streamedContent = '';
    let finalMistakes = null;

    try {
      // 使用流式API
      const response = await fetch(`${API_BASE_URL}/api/detect/mistakes/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_data: image.data,
          image_type: image.type,
          user_marks: marks
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // 读取流式响应
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // 处理SSE格式的数据
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              // 错误处理
              if (data.error) {
                setConversation(prev => prev.map(msg =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: `抱歉，${data.error}` }
                    : msg
                ));
                return;
              }

              // 状态更新
              if (data.status) {
                console.log('[detectMistakes SSE] 收到状态:', data.status, data.message);
                // 状态消息不改变showAnalyzing，让"AI正在分析中"保持显示
                // 只有收到实际内容(data.content)时才移除showAnalyzing
                if (data.status === 'start') {
                  setConversation(prev => prev.map(msg =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: data.message || '' }
                      : msg
                  ));
                } else if (data.status === 'processing' || data.status === 'analyzing') {
                  // 追加状态消息
                  streamedContent += (streamedContent ? '\n\n' : '') + (data.message || '');
                  setConversation(prev => prev.map(msg =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: streamedContent }
                      : msg
                  ));
                } else if (data.status === 'found') {
                  // 找到错题
                  streamedContent += (streamedContent ? '\n\n' : '') + (data.message || '');
                  setConversation(prev => prev.map(msg =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: streamedContent }
                      : msg
                  ));
                } else if (data.status === 'no_mistakes') {
                  setConversation(prev => prev.map(msg =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: data.message || '✅ 没有发现明显的错题标记。这张试卷看起来做得很好！' }
                      : msg
                  ));
                }
              }

              // 内容更新（学情分析）- 只有收到实际内容时才移除showAnalyzing
              if (data.content) {
                console.log('[detectMistakes SSE] 收到内容:', data.content);
                streamedContent += data.content;
                setConversation(prev => prev.map(msg =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: streamedContent, showAnalyzing: false }
                    : msg
                ));
              }

              // 完成，获取最终数据
              if (data.done && data.data) {
                finalMistakes = data.data.mistakes || [];

                if (finalMistakes.length > 0) {
                  setDetectedMistakes(finalMistakes);

                  // 保存分析到历史记录
                  saveAnalysisToHistory(finalMistakes, streamedContent, image);

                  // 显示确认消息
                  const mistakeList = finalMistakes.map((m, idx) =>
                    `${idx + 1}. 题号 ${m.question_no || '?'}`
                  ).join('\n');

                  const confirmMessage = `🔍 **检测到 ${finalMistakes.length} 道错题**

${mistakeList}

---

⚠️ **请确认**: 以上 ${finalMistakes.length} 道题是真正的错题吗？

请回复:
- 输入确认的题号 (如: 1,3,5) 只对这些题目进行苏格拉底式引导
- 或输入"全部" 对所有题目进行引导
- 或输入"重新检测" 上传新的图片`;

                  setConversation(prev => {
                    // 更新当前消息为确认消息
                    const updated = prev.map(msg =>
                      msg.id === assistantMessageId
                        ? {
                            ...msg,
                            content: confirmMessage,
                            interactive: true,
                            options: [
                              { label: "只对部分题目引导", description: "选择特定题号进行引导式学习" },
                              { label: "全部引导", description: "对所有错题逐一引导" },
                              { label: "重新检测", description: "上传新的试卷图片" }
                            ]
                          }
                        : msg
                    );
                    return updated;
                  });
                }
              }

            } catch (parseError) {
              console.error('解析SSE数据失败:', parseError, line);
            }
          }
        }
      }

    } catch (error) {
      console.error('检测失败:', error);
      setConversation(prev => prev.map(msg =>
        msg.id === assistantMessageId
          ? { ...msg, content: '抱歉，错题检测失败。请重试或手动说明需要帮助的题目。' }
          : msg
      ));
    } finally {
      setPendingRequests(prev => {
        const newValue = Math.max(0, prev - 1);
        if (newValue <= 0) {
          setIsThinking(false);
        }
        return newValue;
      });
    }
  };

  // 处理错题图片上传
  const handleImageUploadForMistake = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // 验证文件
    if (file.size > 10 * 1024 * 1024) {
      showToast('图片文件过大,请上传小于10MB的图片', 'error');
      e.target.value = '';
      return;
    }

    if (!file.type.startsWith('image/')) {
      showToast('请上传图片文件', 'error');
      e.target.value = '';
      return;
    }

    setPendingRequests(prev => prev + 1);
    setIsThinking(true);

    const reader = new FileReader();
    reader.onload = async (event) => {
      const base64Data = event.target.result.split(',')[1];
      const mediaType = file.type;
      const imageData = {
        data: base64Data,
        type: mediaType,
        preview: event.target.result
      };

      try {
        const response = await fetch(`${API_BASE_URL}/api/analyze/question`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            image_data: base64Data,
            image_type: mediaType
          })
        });

        if (!response.ok) {
          throw new Error('识别失败');
        }

        const data = await response.json();

        if (data.success && data.data) {
          const newMistake = {
            id: Date.now(),
            question: data.data.question || '未知题目',
            subject: data.data.subject || '未知',
            topic: data.data.topic || '',
            difficulty: data.data.difficulty || '中等',
            correctAnswer: data.data.correctAnswer || '',
            yourAnswer: data.data.yourAnswer || '待补充',
            errorReason: data.data.errorReason || '',
            addedAt: new Date().toISOString(),
            image: imageData,
            reviewed: false,
            autoAdded: true,
            reviewHistory: []
          };

          setMistakes(prev => [newMistake, ...prev]);
          showToast('✅ 错题已成功识别并添加到错题本！', 'success');
          e.target.value = ''; // 清空input以便重复上传
        } else {
          const errorMsg = data.error || '识别失败，请重试';
          showToast(`❌ ${errorMsg}`, 'error');
        }
      } catch (error) {
        console.error('Error:', error);
        showToast('识别失败，请重试', 'error');
      } finally {
        setPendingRequests(prev => {
          const newValue = Math.max(0, prev - 1);
          if (newValue <= 0) {
            setIsThinking(false);
          }
          return newValue;
        });
      }
    };

    reader.onerror = () => {
      showToast('图片读取失败，请重试', 'error');
      setPendingRequests(prev => Math.max(0, prev - 1));
      setIsThinking(false);
      e.target.value = '';
    };

    reader.readAsDataURL(file);
  };

  // 标记已复习
  const markAsReviewed = (mistakeId) => {
    setMistakes(prev => prev.map(m => {
      if (m.id === mistakeId) {
        return {
          ...m,
          reviewed: true,
          reviewHistory: [...(m.reviewHistory || []), {
            date: new Date().toISOString(),
            correct: true
          }]
        };
      }
      return m;
    }));
  };

  // 生成针对性练习
  const generatePracticeForWeakPoint = async (subject, topic, caseStudy) => {
    setPendingRequests(prev => prev + 1);
    setIsThinking(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: `请为${subject}的"${topic}"知识点生成5道针对性练习题。

参考案例：
- 典型问题：${caseStudy.problem}
- 常见错误：${caseStudy.commonMistake}
- 解题方法：${caseStudy.solution}

要求：
1. 题目难度从易到难，循序渐进
2. 每道题都要针对常见错误点设计
3. 包含题目、选项（如适用）、答案和详细解析
4. 解析要点明易错点和正确思路

请以清晰的格式输出题目和解析。`,
          conversation_history: []
        })
      });

      const data = await response.json();

      if (data.success) {
        showToast(`✅ 已为"${topic}"生成针对性练习题！`, 'success');
        // 在对话区域显示结果
        setConversation(prev => [...prev, {
          role: 'assistant',
          content: data.response
        }]);
      } else {
        showToast(`生成失败：${data.error || '请稍后再试'}`, 'error');
      }
    } catch (error) {
      console.error('Error:', error);
      showToast('生成失败，请稍后再试', 'error');
    } finally {
      setPendingRequests(prev => {
        const newValue = Math.max(0, prev - 1);
        if (newValue <= 0) {
          setIsThinking(false);
        }
        return newValue;
      });
    }
  };

  // 生成学科练习
  const generateSubjectQuiz = async (subjectName, weakPoints) => {
    setPendingRequests(prev => prev + 1);
    setIsThinking(true);

    try {
      const weakPointsInfo = weakPoints && weakPoints.length > 0
        ? `\n重点关注的薄弱知识点：\n${weakPoints.map(wp => `- ${wp.topic}（当前掌握度${wp.score}%）`).join('\n')}`
        : '';

      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: `请为${subjectName}生成${quizParams.count}道${quizParams.difficulty}难度的练习题。
${weakPointsInfo}

要求：
1. 题目难度：${quizParams.difficulty === '混合' ? '从易到难，循序渐进' : quizParams.difficulty}
2. 如果有薄弱知识点，请重点覆盖这些知识点
3. 每道题包含：
   - 题目内容
   - 选项（如果是选择题）
   - 正确答案
   - 详细解析（包含解题思路和易错点）
4. 题目要有实际考查价值，贴近真实考试

请按以下格式输出：

【题目1】（难度：基础/中等/困难）
题干：...
A. ...
B. ...
C. ...
D. ...
答案：B
解析：...
易错点：...

【题目2】
...`,
          conversation_history: []
        })
      });

      const data = await response.json();

      if (data.success) {
        showToast(`✅ 已生成${subjectName}练习题！`, 'success');
        // 显示在对话区域
        setActiveTab('solve');
        setConversation([{
          role: 'assistant',
          content: data.response
        }]);
      } else {
        showToast(`生成失败：${data.error || '请稍后再试'}`, 'error');
      }
    } catch (error) {
      console.error('Error:', error);
      showToast('生成失败，请稍后再试', 'error');
    } finally {
      setPendingRequests(prev => {
        const newValue = Math.max(0, prev - 1);
        if (newValue <= 0) {
          setIsThinking(false);
        }
        return newValue;
      });
    }
  };

  // 生成学习报告
  const generateLearningReport = async () => {
    if (!learningData) {
      showToast('暂无学习数据，请先进行错题分析', 'error');
      return;
    }

    setPendingRequests(prev => prev + 1);
    setIsThinking(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: `请生成一份完整的学习分析报告。

基本数据：
- 学习时长：${learningData.weeklyHours}小时
- 完成题目：${learningData.questionsCompleted}道
- 正确率：${learningData.accuracy}%

各科情况：
${learningData.subjectAnalysis.map(s => `${s.name}: ${s.accuracy}% (${s.change > 0 ? '+' : ''}${s.change}%)`).join('\n')}

请生成一份鼓励性的、可操作的学习报告，包含：
1. 整体评价
2. 进步点和需要关注的地方
3. 具体建议`,
          conversation_history: []
        })
      });

      const data = await response.json();

      if (data.success) {
        showToast('📊 学习报告生成成功！', 'success');
        // 显示在对话区域
        setActiveTab('solve');
        setConversation([{
          role: 'assistant',
          content: '📊 **完整学习报告**\n\n' + data.response
        }]);
      } else {
        showToast(`生成失败：${data.error || '请稍后再试'}`, 'error');
      }
    } catch (error) {
      console.error('Error:', error);
      showToast('生成失败，请稍后再试', 'error');
    } finally {
      setPendingRequests(prev => {
        const newValue = Math.max(0, prev - 1);
        if (newValue <= 0) {
          setIsThinking(false);
        }
        return newValue;
      });
    }
  };

  // ==================== Solvely UI 渲染 ====================
  return (
    <div className="min-h-screen" style={{ backgroundColor: '#F5F7FA' }}>
      {/* Toast 通知 */}
      {toast && (
        <div className={`fixed top-20 right-4 z-[100] px-6 py-3 rounded-lg shadow-lg transition-all transform ${
          toast.type === 'success' ? 'bg-green-600' :
          toast.type === 'error' ? 'bg-red-600' :
          'bg-blue-600'
        } text-white max-w-md`}>
          <div className="flex items-center gap-3">
            {toast.type === 'success' && <Check className="w-5 h-5" />}
            {toast.type === 'error' && <AlertCircle className="w-5 h-5" />}
            {toast.type === 'info' && <Sparkles className="w-5 h-5" />}
            <span className="text-sm font-medium">{toast.message}</span>
          </div>
        </div>
      )}

      {/* Solvely 风格头部 */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="flex justify-between items-center h-16 px-6">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #3b82f6, #2563eb)' }}>
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-lg font-semibold" style={{ color: '#374151' }}>伴学AI</h1>
          </div>
        </div>
      </header>

      {/* Solvely 风格左侧边栏导航 */}
      <div className="flex" style={{ backgroundColor: '#f8f9fa' }}>
        {/* 左侧边栏 - 桌面端显示 */}
        <aside className="hidden md:block md:fixed md:left-0 md:top-16 md:h-[calc(100vh-4rem)] md:w-64 md:z-40 md:overflow-y-auto" style={{ backgroundColor: '#f8f9fa' }}>
          <nav className="p-4 space-y-1">
            {[
              { id: 'solve', label: 'AI解题', icon: BookOpen },
              { id: 'mistakes', label: '错题本', icon: AlertCircle },
              { id: 'analysis', label: '学习分析', icon: BarChart3 },
              { id: 'quiz', label: '练习生成', icon: Target }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${
                  activeTab === tab.id
                    ? 'text-blue-600'
                    : 'text-gray-700 hover:bg-gray-200'
                }`}
              >
                <tab.icon className={`w-5 h-5 ${activeTab === tab.id ? 'text-blue-600' : 'text-gray-500'}`} />
                <span className="font-medium text-sm">{tab.label}</span>
              </button>
            ))}
          </nav>

          {/* 底部 Apps 区域 */}
          <div className="absolute bottom-4 left-4 right-4">
            <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-700 hover:bg-gray-200 transition-all relative">
              <div className="w-5 h-5 relative">
                <div className="w-5 h-5 grid grid-cols-2 gap-0.5">
                  <div className="bg-gray-500 rounded-sm"></div>
                  <div className="bg-gray-500 rounded-sm"></div>
                  <div className="bg-gray-500 rounded-sm"></div>
                  <div className="bg-gray-500 rounded-sm"></div>
                </div>
                {/* 通知红点 */}
                <div className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-red-500 rounded-full"></div>
              </div>
              <span className="font-medium text-sm">Apps</span>
            </button>
          </div>
        </aside>

        {/* 主内容区域 */}
        <main className="ml-0 md:ml-64 flex-1 min-h-[calc(100vh-4rem)] bg-white pb-20 md:pb-0">
          <div className="max-w-4xl mx-auto px-8 py-8">
        {/* AI解题标签 */}
        {activeTab === 'solve' && (
          <div className="space-y-6">
            {/* 顶部操作按钮 */}
            <div className="flex justify-between items-center">
              <button
                onClick={() => {
                  // 清空所有状态
                  setConversation([]);
                  setQuestion('');
                  setUploadedImage(null);
                  setIsGuidanceMode(false);
                  setCurrentDiagnosis(null);
                  setGuidanceConversation([]);
                  setDetectedMistakes([]);
                }}
                className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <Plus className="w-4 h-4" />
                <span className="text-sm font-medium">New question</span>
              </button>
              <button
                onClick={() => {
                  setHistoryTab('conversation');
                  setShowHistory(true);
                }}
                className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors relative"
              >
                <Clock className="w-4 h-4" />
                <span className="text-sm font-medium">History</span>
                {(conversationHistory.length > 0 || analysisHistory.length > 0) && (
                  <span className="absolute -top-1 -right-1 w-5 h-5 bg-blue-600 text-white text-xs rounded-full flex items-center justify-center">
                    {conversationHistory.length + analysisHistory.length}
                  </span>
                )}
              </button>
            </div>

            {/* 历史记录对话框 */}
            {showHistory && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[80vh] overflow-hidden">
                  <div className="flex items-center justify-between p-6 border-b border-gray-200">
                    <h2 className="text-xl font-semibold text-gray-800">历史记录</h2>
                    <button
                      onClick={() => setShowHistory(false)}
                      className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      <X className="w-5 h-5 text-gray-600" />
                    </button>
                  </div>

                  {/* 标签页切换 */}
                  <div className="flex border-b border-gray-200">
                    <button
                      className={`flex-1 px-6 py-3 text-sm font-medium ${historyTab === 'conversation' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
                      onClick={() => setHistoryTab('conversation')}
                    >
                      对话历史 ({conversationHistory.length})
                    </button>
                    <button
                      className={`flex-1 px-6 py-3 text-sm font-medium ${historyTab === 'analysis' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
                      onClick={() => setHistoryTab('analysis')}
                    >
                      错题分析 ({analysisHistory.length})
                    </button>
                  </div>

                  <div className="p-6 overflow-y-auto max-h-[55vh]">
                    {historyTab === 'conversation' ? (
                      // 对话历史
                      conversationHistory.length === 0 ? (
                        <div className="text-center py-12">
                          <Clock className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                          <p className="text-gray-600 mb-2">还没有对话历史</p>
                          <p className="text-sm text-gray-500">开始对话后，记录会自动保存在这里</p>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          {conversationHistory.map((item) => (
                            <div
                              key={item.id}
                              className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-md transition-all cursor-pointer"
                              onClick={() => {
                                setConversation(item.conversation);
                                setShowHistory(false);
                              }}
                            >
                              <div className="flex items-start justify-between mb-2">
                                <div className="flex items-center gap-2">
                                  {item.hasImage && <Image className="w-4 h-4 text-blue-600" />}
                                  <span className="text-sm font-medium text-gray-800">
                                    {item.preview}
                                  </span>
                                </div>
                                <span className="text-xs text-gray-500">
                                  {new Date(item.timestamp).toLocaleString('zh-CN', {
                                    month: 'short',
                                    day: 'numeric',
                                    hour: '2-digit',
                                    minute: '2-digit'
                                  })}
                                </span>
                              </div>
                              <div className="text-xs text-gray-500">
                                {item.conversation.length} 条消息
                              </div>
                            </div>
                          ))}
                        </div>
                      )
                    ) : (
                      // 错题分析历史
                      analysisHistory.length === 0 ? (
                        <div className="text-center py-12">
                          <FileText className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                          <p className="text-gray-600 mb-2">还没有错题分析记录</p>
                          <p className="text-sm text-gray-500">上传试卷进行错题检测后，记录会保存在这里</p>
                        </div>
                      ) : (
                        <div className="space-y-4">
                          {analysisHistory.map((item) => (
                            <div
                              key={item.id}
                              className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-md transition-all"
                            >
                              <div className="flex items-start justify-between mb-3">
                                <div className="flex-1">
                                  <h3 className="font-medium text-gray-800 mb-1">{item.preview}</h3>
                                  <p className="text-xs text-gray-500">
                                    {new Date(item.timestamp).toLocaleString('zh-CN', {
                                      year: 'numeric',
                                      month: 'long',
                                      day: 'numeric',
                                      hour: '2-digit',
                                      minute: '2-digit'
                                    })}
                                  </p>
                                </div>
                                <div className="flex gap-2">
                                  <button
                                    className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                                    onClick={() => {
                                      // 查看详情
                                      setShowHistory(false);
                                      setUploadedImage(item.image);
                                      setConversation([
                                        {
                                          role: 'assistant',
                                          content: `📊 **历史分析记录**\n\n检测到 ${item.mistakeCount} 道错题\n\n${item.mistakes.map((m, i) => `${i + 1}. 第${m.question_no}题`).join('\n')}\n\n---\n\n${item.analysis}`
                                        }
                                      ]);
                                    }}
                                  >
                                    查看详情
                                  </button>
                                  <button
                                    className="px-3 py-1 text-xs bg-red-100 text-red-600 rounded hover:bg-red-200 transition-colors"
                                    onClick={() => {
                                      if (confirm('确定删除这条分析记录吗？')) {
                                        const newHistory = analysisHistory.filter(h => h.id !== item.id);
                                        setAnalysisHistory(newHistory);
                                        localStorage.setItem('analysisHistory', JSON.stringify(newHistory));
                                      }
                                    }}
                                  >
                                    删除
                                  </button>
                                </div>
                              </div>

                              {/* 错题列表 */}
                              <div className="mb-3">
                                <p className="text-xs font-medium text-gray-600 mb-2">检测到的错题：</p>
                                <div className="flex flex-wrap gap-2">
                                  {item.mistakes.map((mistake, idx) => (
                                    <span key={idx} className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded">
                                      第{mistake.question_no}题
                                    </span>
                                  ))}
                                </div>
                              </div>

                              {/* 缩略图 */}
                              {item.image && (
                                <div className="mt-2">
                                  <img
                                    src={item.image.preview}
                                    alt="试卷缩略图"
                                    className="w-32 h-auto rounded border border-gray-200 cursor-pointer hover:border-blue-400"
                                    onClick={() => {
                                      setShowImageModal(true);
                                      setModalImage(item.image);
                                    }}
                                  />
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )
                    )}
                  </div>

                  <div className="p-4 border-t border-gray-200 bg-gray-50">
                    <button
                      onClick={() => {
                        if (confirm('确定要清空所有历史记录吗？')) {
                          if (historyTab === 'conversation') {
                            setConversationHistory([]);
                            localStorage.removeItem('conversationHistory');
                          } else {
                            setAnalysisHistory([]);
                            localStorage.removeItem('analysisHistory');
                          }
                        }
                      }}
                      className="w-full px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors text-sm font-medium"
                    >
                      清空{historyTab === 'conversation' ? '对话' : '分析'}历史
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* 主要内容区域 - 使用 flex 布局固定输入框 */}
            <div className="flex flex-col" style={{ height: 'calc(100vh - 200px)' }}>
              {/* 对话区域 - 可滚动 */}
              <div className="flex-1 overflow-y-auto space-y-4 mb-4">
                {/* 上传/预览区域 */}
                {!uploadedImage && conversation.length === 0 && (
                  <div className="border-2 border-dashed border-gray-300 rounded-xl p-12 text-center hover:border-blue-400 transition-colors bg-gray-50">
                    <Upload className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                    <p className="text-lg font-medium text-gray-700 mb-2">上传你的学习资料</p>
                    <p className="text-sm text-gray-500 mb-4">支持图片、PDF等格式</p>
                    <label className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer">
                      <Plus className="w-5 h-5" />
                      <span className="font-medium">选择文件</span>
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        onChange={handleImageUpload}
                        className="hidden"
                        disabled={isThinking}
                      />
                    </label>
                  </div>
                )}

                {/* 对话消息 */}
                {conversation.map((msg, idx) => (
                  <div key={msg.id || idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    {msg.role === 'assistant' && (
                      <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0 mr-2">
                        <Sparkles className="w-5 h-5 text-white" />
                      </div>
                    )}
                    <div className={`max-w-xl px-4 py-3 rounded-lg text-left ${
                      msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-900'
                    }`}>
                      {msg.image && (
                        <img
                          src={msg.image.preview}
                          alt="上传的图片"
                          className="max-w-sm w-full rounded-lg mb-2"
                        />
                      )}
                      {/* 调试信息 */}
                      {console.log('[渲染] 消息渲染:', {
                        id: msg.id,
                        showAnalyzing: msg.showAnalyzing,
                        hasContent: !!msg.content,
                        contentLength: msg.content?.length || 0
                      })}
                      {/* 内容显示逻辑 */}
                      {msg.showAnalyzing && (!msg.content || msg.content.length === 0) ? (
                        <div className="flex items-center gap-3 text-blue-600" data-test="loading-spinner">
                          <RefreshCw className="w-5 h-5 animate-spin" />
                          <span className="text-base font-medium">AI 正在分析中...</span>
                        </div>
                      ) : msg.content && msg.content.length > 0 ? (
                        <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>

              {/* 输入区域 - 固定在底部 */}
              <div className={`border rounded-lg p-4 shadow-sm flex-shrink-0 ${isGuidanceMode ? 'bg-blue-50 border-blue-300' : 'bg-white border-gray-200'}`}>
                {/* 引导模式提示 */}
                {isGuidanceMode && (
                  <div className="mb-3 p-2 bg-blue-100 border border-blue-200 rounded-lg flex items-center gap-2">
                    <Brain className="w-5 h-5 text-blue-600" />
                    <span className="text-sm text-blue-700 font-medium">
                      👨‍🏫 引导模式中 - 回答老师的问题，或输入"退出引导"返回
                    </span>
                  </div>
                )}

                <textarea
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSolveQuestion();
                    }
                  }}
                  placeholder={
                    isGuidanceMode
                      ? "请回答老师的问题..."
                      : uploadedImage
                      ? '输入问题，或直接点击"分析"按钮'
                      : '输入你的问题...（上传图片后可说"不会"或"错了"启动诊断）'
                  }
                  className="w-full resize-none outline-none text-gray-700 placeholder-gray-400 bg-transparent"
                  rows="1"
                  disabled={isThinking}
                />
                <div className="flex justify-between items-center mt-3 pt-3 border-t border-gray-200">
                  <label className="flex items-center gap-2 px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer">
                    <Image className="w-5 h-5" />
                    <span className="text-sm">上传图片</span>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleImageUpload}
                      className="hidden"
                      disabled={isThinking || isGuidanceMode}
                    />
                  </label>
                  <button
                    onClick={handleSolveQuestion}
                    disabled={(!question.trim() && !uploadedImage) || isThinking}
                    className={`flex items-center gap-2 px-6 py-2.5 text-white rounded-lg transition-colors font-medium ${
                      isGuidanceMode
                        ? 'bg-purple-600 hover:bg-purple-700 disabled:bg-purple-300'
                        : uploadedImage && !question.trim()
                        ? 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:opacity-50'
                        : 'bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300'
                    }`}
                  >
                    {isThinking ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span>发送中...</span>
                      </>
                    ) : (
                      <>
                        {isGuidanceMode ? (
                          <>
                            <Sparkles className="w-4 h-4" />
                            <span>回答</span>
                          </>
                        ) : uploadedImage && !question.trim() ? (
                          <>
                            <AlertCircle className="w-4 h-4" />
                            <span>分析</span>
                          </>
                        ) : (
                          <>
                            <Sparkles className="w-4 h-4" />
                            <span>发送</span>
                          </>
                        )}
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 错题本标签 */}
        {activeTab === 'mistakes' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold text-gray-800">错题本</h2>
              <label className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer">
                <Upload className="w-4 h-4" />
                <span className="text-sm font-medium">上传错题</span>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageUploadForMistake}
                  className="hidden"
                  disabled={isThinking}
                />
              </label>
            </div>

            {isThinking && (
              <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
                <div className="flex items-center gap-3">
                  <RefreshCw className="w-5 h-5 animate-spin text-blue-600" />
                  <p className="text-blue-700">正在识别题目信息...</p>
                </div>
              </div>
            )}

            <div className="grid gap-4">
              {mistakes.length === 0 ? (
                <div className="bg-white border border-gray-200 p-12 text-center rounded-lg">
                  <AlertCircle className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                  <p className="text-gray-600 mb-2">还没有错题记录</p>
                  <p className="text-sm text-gray-500">点击"上传错题"开始整理</p>
                </div>
              ) : (
                mistakes.map(mistake => (
                  <div key={mistake.id} className="bg-white border border-gray-200 rounded-lg p-5 hover:shadow-md transition-shadow">
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex gap-2 flex-wrap">
                        <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">{mistake.subject}</span>
                        {mistake.topic && (
                          <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm">{mistake.topic}</span>
                        )}
                        {mistake.autoAdded && (
                          <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm flex items-center gap-1">
                            <Sparkles className="w-3 h-3" />
                            AI识别
                          </span>
                        )}
                        {mistake.reviewed && (
                          <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm flex items-center gap-1">
                            <Check className="w-3 h-3" />
                            已复习
                          </span>
                        )}
                      </div>
                      <span className="text-sm text-gray-500">{new Date(mistake.addedAt).toLocaleDateString()}</span>
                    </div>

                    {mistake.image && (
                      <div className="mb-4">
                        <img
                          src={mistake.image.preview}
                          alt="题目图片"
                          className="max-w-full rounded-lg border border-gray-200"
                        />
                      </div>
                    )}

                    <p className="mb-4 font-medium text-gray-800">{mistake.question}</p>

                    {mistake.errorReason && (
                      <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                        <p className="text-sm text-yellow-800">
                          <span className="font-semibold">错误原因：</span>{mistake.errorReason}
                        </p>
                      </div>
                    )}

                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-sm mb-1 text-gray-600">你的答案</p>
                        <p className="font-medium text-red-700">{mistake.yourAnswer}</p>
                      </div>
                      <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                        <p className="text-sm mb-1 text-gray-600">正确答案</p>
                        <p className="font-medium text-green-700">{mistake.correctAnswer}</p>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      {!mistake.reviewed && (
                        <button
                          onClick={() => markAsReviewed(mistake.id)}
                          className="flex-1 px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 text-sm font-medium transition-colors"
                        >
                          标记已复习
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* 学习分析标签 */}
        {activeTab === 'analysis' && learningData && (
          <div className="space-y-6">
            <div className="flex items-center gap-4 mb-6">
              <h2 className="text-xl font-semibold text-gray-800">学习分析报告</h2>
              <p className="text-sm text-gray-500">本周学习总结 · 分学科提分方案</p>
            </div>

            {/* 统计卡片 */}
            <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg p-6 shadow-lg">
              <h3 className="text-xl font-bold mb-4 text-white">📊 本周学习总结</h3>

              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-white rounded-lg p-4 text-center">
                  <p className="text-3xl font-bold text-blue-600">{learningData.weeklyHours}h</p>
                  <p className="text-sm mt-1 text-gray-600">学习时长</p>
                </div>
                <div className="bg-white rounded-lg p-4 text-center">
                  <p className="text-3xl font-bold text-blue-600">{learningData.questionsCompleted}题</p>
                  <p className="text-sm mt-1 text-gray-600">完成题目</p>
                </div>
                <div className="bg-white rounded-lg p-4 text-center">
                  <p className="text-3xl font-bold text-green-600">{learningData.accuracy}%</p>
                  <p className="text-sm mt-1 text-gray-600">总体正确率</p>
                </div>
              </div>

              <div className="bg-white rounded-lg p-4 mb-4">
                <p className="text-gray-800">{learningData.weekSummary.overview}</p>
              </div>

              <div className="space-y-2">
                {learningData.weekSummary.changes.map((change, idx) => (
                  <div key={idx} className={`flex items-start gap-2 p-3 rounded-lg ${
                    change.type === 'positive' ? 'bg-green-100' : 'bg-yellow-100'
                  }`}>
                    {change.type === 'positive' ? (
                      <TrendingUp className="w-5 h-5 flex-shrink-0 mt-0.5 text-green-600" />
                    ) : (
                      <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-yellow-600" />
                    )}
                    <span className={`text-sm ${
                      change.type === 'positive' ? 'text-green-800' : 'text-yellow-800'
                    }`}>
                      {change.text}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* 学科分析 */}
            <div className="space-y-6">
              <h3 className="text-xl font-semibold text-gray-800">📚 分学科提分方案</h3>

              {learningData.subjectAnalysis.map((subject, idx) => (
                <div key={subject.name} className="bg-white border border-gray-200 rounded-lg p-6">
                  <div className="flex justify-between items-center mb-6 pb-4 border-b-2 border-gray-100">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-blue-100">
                        <span className="text-xl font-bold text-blue-600">{idx + 1}</span>
                      </div>
                      <div>
                        <h4 className="text-xl font-semibold text-gray-800">{subject.name}</h4>
                        <p className="text-sm text-gray-600">正确率 {subject.accuracy}%</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-blue-600">{subject.accuracy}%</p>
                      {subject.change !== 0 && (
                        <p className={`text-sm ${
                          subject.change > 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {subject.change > 0 ? '↑' : '↓'} {Math.abs(subject.change)}%
                        </p>
                      )}
                    </div>
                  </div>

                  {subject.weakPoints && subject.weakPoints.length > 0 ? (
                    <div className="space-y-6">
                      {subject.weakPoints.map((wp, wpIdx) => (
                        <div key={wp.topic} className="p-5 rounded-lg border-2 border-red-200 bg-red-50">
                          <div className="flex justify-between items-start mb-4">
                            <div>
                              <h5 className="text-lg font-semibold text-gray-800">{wp.topic}</h5>
                              <p className="text-sm mt-1 text-gray-600">{wp.description}</p>
                            </div>
                            <p className="text-2xl font-bold text-red-600">{wp.score}%</p>
                          </div>

                          <div className="bg-white rounded-lg p-4 mb-4">
                            <h6 className="font-semibold mb-3 text-gray-800">典型案例分析</h6>
                            <div className="space-y-3 text-sm">
                              <div className="p-3 rounded-lg bg-blue-50">
                                <p className="font-medium mb-1 text-blue-800">📝 典型问题</p>
                                <p className="text-blue-900">{wp.caseStudy.problem}</p>
                              </div>
                              <div className="p-3 rounded-lg bg-red-50">
                                <p className="font-medium mb-1 text-red-800">❌ 常见错误</p>
                                <p className="text-red-900">{wp.caseStudy.commonMistake}</p>
                              </div>
                              <div className="p-3 rounded-lg bg-green-50">
                                <p className="font-medium mb-1 text-green-800">✅ 正确方法</p>
                                <p className="text-green-900">{wp.caseStudy.solution}</p>
                              </div>
                            </div>
                          </div>

                          <button
                            onClick={() => generatePracticeForWeakPoint(subject.name, wp.topic, wp.caseStudy)}
                            disabled={isThinking}
                            className="w-full py-3 text-white rounded-lg font-medium flex items-center justify-center gap-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 transition-all"
                          >
                            {isThinking ? (
                              <>
                                <RefreshCw className="w-5 h-5 animate-spin" />
                                生成中...
                              </>
                            ) : (
                              <>
                                <Target className="w-5 h-5" />
                                生成【{wp.topic}】针对性练习题
                              </>
                            )}
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-6 rounded-lg bg-green-50">
                      <Award className="w-12 h-12 mx-auto mb-2 text-green-600" />
                      <p className="font-medium text-green-700">该科目掌握良好！</p>
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="rounded-lg p-6 bg-gradient-to-br from-purple-100 to-pink-100 border-2 border-purple-200">
              <div className="text-center">
                <h3 className="text-2xl font-bold mb-2 text-gray-800">4周总提分预期</h3>
                <p className="text-5xl font-bold mb-4 text-purple-600">+{learningData.totalEstimatedImprovement}分</p>
              </div>
            </div>

            <button
              onClick={generateLearningReport}
              disabled={isThinking}
              className="w-full py-4 text-white rounded-lg font-semibold text-lg flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 transition-all"
            >
              {isThinking ? (
                <>
                  <RefreshCw className="w-5 h-5 animate-spin" />
                  生成中...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  生成完整AI学习报告
                </>
              )}
            </button>
          </div>
        )}

        {/* 练习生成标签 */}
        {activeTab === 'quiz' && (
          <div className="space-y-6">
            <div className="flex items-center gap-4 mb-6">
              <h2 className="text-xl font-semibold text-gray-800">个性化练习生成</h2>
              <p className="text-sm text-gray-500">基于你的学习情况智能生成</p>
            </div>

            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800">按学科生成练习</h3>

              {learningData && learningData.subjectAnalysis.map((subject) => (
                <div key={subject.name} className="bg-white border border-gray-200 rounded-lg p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h4 className="text-xl font-semibold mb-1 text-gray-800">{subject.name}</h4>
                      <p className="text-sm text-gray-600">
                        当前正确率：{subject.accuracy}%
                        <span className={`ml-2 ${
                          subject.change > 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          ({subject.change > 0 ? '+' : ''}{subject.change}%)
                        </span>
                      </p>
                    </div>
                    <div className="text-right">
                      <p className={`text-2xl font-bold ${
                        subject.accuracy >= 85 ? 'text-green-600' : subject.accuracy >= 70 ? 'text-yellow-600' : 'text-red-600'
                      }`}>
                        {subject.accuracy}%
                      </p>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium mb-2 text-gray-700">题目数量</label>
                      <div className="flex gap-2">
                        {[5, 10, 15, 20].map(count => (
                          <button
                            key={count}
                            onClick={() => setQuizParams({ ...quizParams, count, subject: subject.name })}
                            className={`px-4 py-2 rounded-lg font-medium transition-all ${
                              quizParams.count === count && quizParams.subject === subject.name
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                          >
                            {count}题
                          </button>
                        ))}
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2 text-gray-700">难度等级</label>
                      <div className="flex gap-2">
                        {['基础', '中等', '困难', '混合'].map(diff => (
                          <button
                            key={diff}
                            onClick={() => setQuizParams({ ...quizParams, difficulty: diff, subject: subject.name })}
                            className={`px-4 py-2 rounded-lg font-medium transition-all ${
                              quizParams.difficulty === diff && quizParams.subject === subject.name
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                          >
                            {diff}
                          </button>
                        ))}
                      </div>
                    </div>

                    <button
                      onClick={() => generateSubjectQuiz(subject.name, subject.weakPoints)}
                      disabled={isThinking}
                      className="w-full py-3 text-white rounded-lg font-semibold flex items-center justify-center gap-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 transition-all"
                    >
                      {isThinking ? (
                        <>
                          <RefreshCw className="w-5 h-5 animate-spin" />
                          生成中...
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-5 h-5" />
                          生成 {subject.name} 练习题
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
          </div>
        </main>
      </div>

      {/* 底部导航栏 - 移动端显示 */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50">
        <div className="flex justify-around items-center h-16 px-2">
          {[
            { id: 'solve', label: '解题', icon: BookOpen },
            { id: 'mistakes', label: '错题本', icon: AlertCircle },
            { id: 'analysis', label: '分析', icon: BarChart3 },
            { id: 'quiz', label: '练习', icon: Target }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex flex-col items-center justify-center gap-1 px-3 py-2 rounded-lg transition-all ${
                activeTab === tab.id
                  ? 'text-blue-600'
                  : 'text-gray-500'
              }`}
            >
              <tab.icon className={`w-5 h-5 ${activeTab === tab.id ? 'text-blue-600' : 'text-gray-500'}`} />
              <span className="text-xs font-medium">{tab.label}</span>
            </button>
          ))}
        </div>
      </nav>

      {/* 图片弹窗 */}
      {showImageModal && modalImage && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="relative max-w-6xl max-h-[90vh] overflow-auto bg-white rounded-xl shadow-2xl">
            {/* 关闭按钮 */}
            <button
              onClick={() => {
                setShowImageModal(false);
                setModalImage(null);
                setMarkingMode(false);
                setMarkedErrors([]);
                setBoxes([]);
                setCurrentBox(null);
                setStartPoint(null);
                setImageContainerRef(null);
              }}
              className="absolute top-4 right-4 z-10 w-10 h-10 bg-gray-800 hover:bg-gray-700 text-white rounded-full flex items-center justify-center transition-colors shadow-lg"
            >
              <X className="w-6 h-6" />
            </button>

            {/* 图片区域 */}
            <div className="relative p-4">
              <div className="relative inline-block">
                <img
                  src={modalImage.preview}
                  alt="放大的图片"
                  className="max-w-full max-h-[75vh] object-contain rounded-lg"
                  style={{ pointerEvents: markingMode ? 'none' : 'auto' }}
                  ref={(img) => {
                    if (img && modalImage) {
                      modalImage.imgElement = img;
                    }
                  }}
                />

                {/* 框选标记层 - 直接覆盖在图片上 */}
                {markingMode && (
                  <>
                    {/* 已保存的框选区域 */}
                    {boxes.map((box, index) => (
                      <div
                        key={box.id}
                        className="absolute border-4 border-red-500 bg-red-500/10"
                        style={{
                          left: `${box.x}%`,
                          top: `${box.y}%`,
                          width: `${box.width}%`,
                          height: `${box.height}%`,
                          transform: 'translate(0, 0)',
                          pointerEvents: 'auto'
                        }}
                      >
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setBoxes(prev => prev.filter(b => b.id !== box.id));
                            setMarkedErrors(prev => prev.filter(m => m.id !== box.id));
                          }}
                          className="absolute -top-3 -right-3 w-6 h-6 bg-red-600 text-white rounded-full flex items-center justify-center hover:bg-red-700 shadow-lg text-xs font-bold"
                        >
                          {index + 1}
                        </button>
                      </div>
                    ))}

                    {/* 当前正在拖动的框 */}
                    {currentBox && (
                      <div
                        className="absolute border-4 border-blue-500 bg-blue-500/10 pointer-events-none"
                        style={{
                          left: `${currentBox.x}%`,
                          top: `${currentBox.y}%`,
                          width: `${currentBox.width}%`,
                          height: `${currentBox.height}%`,
                          transform: 'translate(0, 0)'
                        }}
                      />
                    )}

                    {/* 框选交互层 */}
                    <div
                      ref={(div) => {
                        if (div && !imageContainerRef) {
                          setImageContainerRef(div);
                        }
                      }}
                      onMouseDown={(e) => {
                        if (!markingMode || !imageContainerRef) return;
                        setIsDrawing(true);
                        const rect = imageContainerRef.getBoundingClientRect();
                        const x = ((e.clientX || e.touches?.[0].clientX) - rect.left) / rect.width * 100;
                        const y = ((e.clientY || e.touches?.[0].clientY) - rect.top) / rect.height * 100;
                        setStartPoint({ x, y });
                        setCurrentBox({ x, y, width: 0, height: 0 });
                      }}
                      onMouseMove={(e) => {
                        if (!isDrawing || !startPoint || !markingMode || !imageContainerRef) return;
                        e.preventDefault();
                        const rect = imageContainerRef.getBoundingClientRect();
                        const x = ((e.clientX || e.touches?.[0].clientX) - rect.left) / rect.width * 100;
                        const y = ((e.clientY || e.touches?.[0].clientY) - rect.top) / rect.height * 100;

                        const width = x - startPoint.x;
                        const height = y - startPoint.y;

                        setCurrentBox({
                          x: width > 0 ? startPoint.x : x,
                          y: height > 0 ? startPoint.y : y,
                          width: Math.abs(width),
                          height: Math.abs(height)
                        });
                      }}
                      onMouseUp={() => {
                        if (!isDrawing || !currentBox || !markingMode) return;
                        setIsDrawing(false);

                        // 只保存足够大的框（避免误触）
                        if (currentBox.width > 2 && currentBox.height > 2) {
                          setBoxes(prev => [...prev, currentBox]);
                          setMarkedErrors(prev => [...prev, {
                            id: Date.now(),
                            box: currentBox,
                            questionNo: `错题${prev.length + 1}`
                          }]);
                        }

                        setCurrentBox(null);
                        setStartPoint(null);
                      }}
                      onMouseLeave={() => {
                        if (isDrawing) {
                          setIsDrawing(false);
                          setCurrentBox(null);
                          setStartPoint(null);
                        }
                      }}
                      style={{
                        cursor: markingMode ? 'crosshair' : 'default',
                        pointerEvents: markingMode ? 'auto' : 'none',
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: '100%'
                      }}
                    />
                  </>
                )}
              </div>
            </div>

            {/* 工具栏 */}
            <div className="border-t border-gray-200 p-4 bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <button
                    onClick={async () => {
                      if (markingMode && boxes.length > 0) {
                        // 完成标记并直接启动分析
                        setShowImageModal(false);
                        const currentMarks = [...markedErrors];
                        setMarkingMode(false);
                        setMarkedErrors([]);
                        setBoxes([]);
                        setImageContainerRef(null);
                        setCurrentBox(null);
                        await detectMistakes(modalImage, currentMarks);
                      } else if (markingMode && boxes.length === 0) {
                        // 没有标记时只是退出标记模式
                        setMarkingMode(false);
                        setBoxes([]);
                        setImageContainerRef(null);
                        setCurrentBox(null);
                      } else {
                        // 进入标记模式
                        setMarkingMode(true);
                      }
                    }}
                    className={`flex items-center gap-2 px-6 py-3 text-white rounded-lg transition-all font-medium shadow-md ${
                      markingMode
                        ? boxes.length > 0
                          ? 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700'
                          : 'bg-gray-500 hover:bg-gray-600'
                        : 'bg-blue-600 hover:bg-blue-700'
                    }`}
                  >
                    {markingMode ? (
                      <>
                        <Sparkles className="w-5 h-5" />
                        <span>{boxes.length > 0 ? `完成并分析 (${boxes.length}个框选)` : "取消标记"}</span>
                      </>
                    ) : (
                      <>
                        <AlertCircle className="w-5 h-5" />
                        <span>开始标记</span>
                      </>
                    )}
                  </button>

                  {markingMode && boxes.length > 0 && (
                    <button
                      onClick={() => {
                        // 撤销最后一个框
                        setBoxes(prev => {
                          const newBoxes = prev.slice(0, -1);
                          setMarkedErrors(prevMarks => prevMarks.slice(0, -1));
                          return newBoxes;
                        });
                      }}
                      className="flex items-center gap-2 px-6 py-3 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-all font-medium shadow-md"
                    >
                      <RefreshCw className="w-5 h-5" />
                      <span>撤销</span>
                    </button>
                  )}

                  {markingMode && boxes.length > 0 && (
                    <button
                      onClick={() => {
                        setBoxes([]);
                        setImageContainerRef(null);
                        setMarkedErrors([]);
                        setCurrentBox(null);
                      }}
                      className="flex items-center gap-2 px-6 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-all font-medium shadow-md"
                    >
                      <X className="w-5 h-5" />
                      <span>清除所有</span>
                    </button>
                  )}
                </div>

                <div className="text-sm text-gray-600">
                  {markingMode ? (
                    <span className="font-medium text-blue-600">拖动鼠标框选出错题位置（已框选 {boxes.length} 个）</span>
                  ) : (
                    <span>点击「开始标记」按钮开始框选错题</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 页脚 */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-sm text-gray-500">
            <p>AI伴学助手</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

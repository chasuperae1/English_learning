#!/usr/bin/env python3
"""
英语语法学习系统 - 主程序
目标：雅思均分 7.0
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from grammar_learning import (
    init_db, get_overall_progress, add_knowledge_point, add_mistake,
    list_knowledge_points, list_mistakes, get_today_reviews,
    update_mastery_level, mark_mistake_reviewed, schedule_spaced_review,
    complete_review, add_study_session, get_study_stats, search_knowledge
)


def print_progress():
    progress = get_overall_progress()
    print("\n" + "=" * 60)
    print("📊 学习进度总览")
    print("=" * 60)
    print(f"🎯 目标: {progress['goal']['goal_name']}")
    print(f"📚 知识点总数: {progress['knowledge_points_total']}")
    print(f"✅ 已掌握 (4-5级): {progress['knowledge_mastered']}")
    print(f"📈 掌握率: {progress['mastery_percentage']}%")
    print(f"❌ 错题总数: {progress['mistakes_total']}")
    print(f"⏰ 待复习错题: {progress['mistakes_unreviewed']}")
    print(f"⏱️  近30天学习: {progress['study_minutes_30d']} 分钟")
    print("=" * 60 + "\n")


def add_new_knowledge():
    print("\n📝 添加新知识点")
    topic = input("主题: ").strip()
    category = input("分类 (如: 时态/从句/虚拟语气...): ").strip() or None
    content = input("内容 (语法规则说明): ").strip()
    examples = input("例句 (可选): ").strip() or None

    kp_id = add_knowledge_point(topic, content, category, examples)
    schedule_spaced_review(kp_id, 0)
    print(f"✅ 知识点已添加 (ID: {kp_id})，已安排复习计划")


def add_new_mistake():
    print("\n❌ 添加错题")
    question = input("题目/句子: ").strip()
    your_answer = input("你的答案 (可选): ").strip() or None
    correct_answer = input("正确答案 (可选): ").strip() or None
    mistake_type = input("错误类型 (如: 时态错误/介词错误...): ").strip() or None
    reason = input("错误原因分析 (可选): ").strip() or None

    mistake_id = add_mistake(question, your_answer, correct_answer,
                             mistake_type=mistake_type, reason=reason)
    print(f"✅ 错题已添加 (ID: {mistake_id})")


def do_today_reviews():
    reviews = get_today_reviews()
    if not reviews:
        print("\n🎉 今天没有待复习的内容！")
        return

    print(f"\n📖 今日复习 ({len(reviews)} 项)")
    print("-" * 60)

    for i, review in enumerate(reviews, 1):
        print(f"\n[{i}/{len(reviews)}]")
        if review.get('kp_topic'):
            print(f"📚 知识点: {review['kp_topic']}")
            print(f"   内容: {review['kp_content'][:100]}...")
        elif review.get('mistake_question'):
            print(f"❌ 错题: {review['mistake_question'][:100]}...")

        input("\n按 Enter 继续...")

        try:
            mastery = int(input("掌握程度 (0-5): "))
            mastery = max(0, min(5, mastery))
        except ValueError:
            mastery = 2

        if review['knowledge_point_id']:
            update_mastery_level(review['knowledge_point_id'], mastery)
            if mastery < 5:
                schedule_spaced_review(review['knowledge_point_id'], mastery)
        elif review['mistake_id']:
            mark_mistake_reviewed(review['mistake_id'])

        complete_review(review['id'])

    print("\n✅ 今日复习完成！")


def show_knowledge_list():
    kps = list_knowledge_points(limit=20)
    if not kps:
        print("\n还没有知识点")
        return
    print("\n📚 最近的知识点")
    print("-" * 60)
    for kp in kps:
        level = "★" * kp['mastery_level'] + "☆" * (5 - kp['mastery_level'])
        print(f"[{kp['id']}] {kp['topic']} - {level}")
        if kp.get('category'):
            print(f"     分类: {kp['category']}")
        print(f"     {kp['content'][:60]}...")
        print()


def show_mistake_list():
    mistakes = list_mistakes(limit=20)
    if not mistakes:
        print("\n还没有错题记录")
        return
    print("\n❌ 最近的错题")
    print("-" * 60)
    for m in mistakes:
        status = "✅已复习" if m['reviewed'] else "⏰待复习"
        print(f"[{m['id']}] {status} - {m['question'][:60]}...")
        if m.get('mistake_type'):
            print(f"     类型: {m['mistake_type']}")
        print()


def main():
    init_db()

    print("\n" + "=" * 60)
    print("🎓 英语语法学习系统 - 雅思 7.0 目标")
    print("=" * 60)

    while True:
        print_progress()
        print("请选择操作:")
        print("1. 📚 查看知识点列表")
        print("2. ➕ 添加新知识点")
        print("3. ❌ 查看错题列表")
        print("4. ➕ 添加错题")
        print("5. 🔄 今日复习")
        print("6. 🔍 搜索知识点")
        print("7. ⏱️  记录学习时间")
        print("0. 🚪 退出")

        choice = input("\n请输入选项: ").strip()

        if choice == '1':
            show_knowledge_list()
        elif choice == '2':
            add_new_knowledge()
        elif choice == '3':
            show_mistake_list()
        elif choice == '4':
            add_new_mistake()
        elif choice == '5':
            do_today_reviews()
        elif choice == '6':
            keyword = input("搜索关键词: ").strip()
            results = search_knowledge(keyword)
            print(f"\n找到 {len(results)} 条结果")
            for r in results:
                print(f"[{r['id']}] {r['topic']}")
        elif choice == '7':
            try:
                minutes = int(input("学习时长 (分钟): "))
                topics = input("学习内容 (可选): ").strip() or None
                notes = input("笔记 (可选): ").strip() or None
                add_study_session(minutes, topics, notes)
                print("✅ 学习记录已保存")
            except ValueError:
                print("❌ 请输入有效的数字")
        elif choice == '0':
            print("\n👋 再见！继续加油向雅思 7.0 前进！")
            break
        else:
            print("\n❌ 无效选项，请重试")

        input("\n按 Enter 继续...")


if __name__ == '__main__':
    main()

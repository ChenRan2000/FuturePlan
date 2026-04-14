# -*- coding: utf-8 -*-
"""
存款规划计算器
资金来源:
	初始存款:	1,222,237元
	股票总额:	788,200元
	初始双边公积金:	220,000元
	养老金:	41,376元 /年 x 30年 	退休后(60岁)开始领取养老金 = 1,241,280
	预计未来工资收入:	668,000元 /年 x 4年 = 2,672,000
	预计未来股票收入:	140,000元 /年 x 4年 = 560,000
	预计未来公积金收入:	11,634元 /月 x 12个月 x 4年 = 558,432
	
资金固定开销:
	养老金缴纳:36,000元 /年 x 15年 = 540,000元

其中：
    [公积金返回] 在30岁（躺平开始）时一次性返回公积金: 778,432 元
    [股票返回] 在30岁（躺平开始）时一次性返回股票: 560,000 元
    工资是工作阶段每年都发放的

计算公式:
	非工作阶段基本每年基础开销：（初始存款 + 股票余额 + 初始双边公积金 + 预计未来工资收入 + 预计未来股票收入 + 预计未来公积金收入 - 养老金缴纳）/ （不工作年限）
	缴养老阶段存款变动 = 基本每年基础开销 - 年收益
	躺平阶段存款变动 = 基本每年基础开销 - 年收益
	养老阶段存款变动 = 基本每年基础开销 - 年收益 + 养老金领取
	月可用收入 = 年可用收入 / 12 (每年不同)
	确保存款在90岁时刚好耗尽

年末余额(元) =  年初余额(元)  + 存款变动(元)

"""

from tabulate import tabulate


def generate_savings_table(principal, annual_rate, current_age, work_age, retirement_age, target_age,
                               stock_total, stock_annual, pension_annual,
                               pension_total_years, pension_paid_years, pension_contribution,
                               work_year_save=0, work_stock=0, work_years_already=0,
                               work_house_money=0, now_house_money=0, basic_annual_expense=0):
    """
    生成年度储蓄规划表

    Args:
        principal: 初始存款金额
        annual_rate: 年收益率（%）
        current_age: 当前年龄
        work_age: 开始躺平的年龄
        retirement_age: 退休年龄
        target_age: 计划寿命
        stock_total: 股票总额
        stock_annual: 股票每年可领
        pension_annual: 养老金每年
        pension_total_years: 需要交满的总年限
        pension_paid_years: 已缴纳的年限
        pension_contribution: 后续每年缴纳金额
        work_year_save: 工作期间每年存款
        work_stock: 工作期间每年股票
        work_years_already: 已经工作的年限
        work_house_money: 每年双边公积金
        now_house_money: 当前双边公积金

    Returns:
        表格数据列表
    """
    rate = annual_rate / 100
    
    work_years = work_age - current_age
    lying_flat_years = retirement_age - work_age
    retirement_years = target_age - retirement_age
    total_years = target_age - current_age + 1  # 包含90岁
    
    # 计算养老金缴纳相关参数
    pension_years_remaining = max(0, pension_total_years - pension_paid_years)  # 还需要交的年数
    age_to_qualify = work_age + pension_years_remaining  # 交满养老金的年龄
    
    # 养老金从退休年龄开始固定领取
    pension_claim_age = retirement_age
    
    # 计算需要从存款中提取的总额（总可用收入 - 股票总额 - 养老金总额）
    # 然后除以剩余年数得到每年应从存款中提取的金额
    total_pension_contribution = pension_contribution * pension_years_remaining
    total_pension_income = pension_annual * retirement_years
    stock_income_total = stock_total  # 股票总额就是可以领完的所有股票收入
    
    # 从存款中需要提取的总额 = 总可用收入 - 股票收入 - 养老金收入 + 养老金缴纳总额
    # 公式：存款变动总额 = 股票 + 存款 + 养老金 - 缴纳 - 股票 - 养老金 = 存款 - 缴纳
    # 所以：存款变动总额 = principal - total_pension_contribution
    total_deposit_withdrawal_needed = principal - total_pension_contribution
    
    stock_remaining = stock_total
    balance = principal
    stock_depleted = False
    pension_contribution_paid = 1  # 已缴纳的养老金年数
    house_money_returned = False  # 标记公积金是否已返回
    stock_returned = False  # 标记股票是否已返回
    
    # 计算工作期间积累的公积金总额
    # 当前公积金 + 工作期间每年的公积金
    total_house_money = now_house_money + work_house_money * work_years
    
    table_data = []
    
    for year in range(total_years):
        age = current_age + year
        is_final_year = age == target_age  # 90岁是最终结算点
        is_working = age < work_age and not is_final_year  # 工作阶段
        is_retired = age >= retirement_age and not is_final_year
        can_claim_pension = age >= retirement_age  # 退休后开始领取养老金
        years_remaining_from_now = total_years - year  # 从现在到90岁的年数
        
        # 在躺平阶段开始时一次性返回公积金
        if not is_working and not house_money_returned and total_house_money > 0:
            # 公积金一次性返回，增加到余额中
            balance += total_house_money
            balance += stock_remaining
            house_money_returned = True
            stock_returned = True
            print(f"[公积金返回] 在{age}岁（躺平开始）时一次性返回公积金: {total_house_money:,}元")
            print(f"[股票返回] 在{age}岁（躺平开始）时一次性返回股票: {stock_total:,}元")
        
        year_start_balance = balance
        annual_interest = year_start_balance * rate
        
        # 在最终结算点（90岁），不计入任何收入
        if is_final_year:
            stock_withdrawal = 0
            current_pension = 0
            current_pension_contribution = 0
            work_income = 0
            work_stock_add = 0
            # 存款变动 = 年初余额 + 年收益，使年末余额为0
            deposit_withdrawal = year_start_balance + annual_interest
            annual_available_income = deposit_withdrawal
            end_balance = 0
            phase = "终"
            stock_or_pension = 0
            phase_display = "终结"
        else:
            # 工作阶段：增加工作收入和股票
            if is_working:
                work_income = work_year_save
                work_stock_add = work_stock
            else:
                work_income = 0
                work_stock_add = 0
            
            # 计算当年可得股票到手
            # 工作期间不提取股票
            # 股票已经在躺平开始时一次性返回，所以不需要再每年提取
            stock_withdrawal = 0
            
            # 计算当年养老金相关
            # 工作期间不缴纳养老金
            if is_working:
                current_pension_contribution = 0
                current_pension = 0
            elif not can_claim_pension and pension_contribution_paid < pension_years_remaining:
                current_pension_contribution = pension_contribution
                pension_contribution_paid += 1
                current_pension = 0
            else:
                current_pension_contribution = 0
                current_pension = pension_annual if is_retired else 0
            
            # 核心计算逻辑：根据不同阶段使用不同的存款变动公式
            # 工作阶段：不花钱，不提取股票，不担心养老的事情
            if is_working:
                annual_available_income = 0
                deposit_withdrawal = 0
                monthly_available = 0
            else:
                # 调整存款变动，确保在90岁时耗尽
                if age == target_age - 1:  # 最后一年
                    deposit_withdrawal = year_start_balance + annual_interest
                    annual_available_income = deposit_withdrawal - current_pension_contribution + current_pension
                    monthly_available = annual_available_income / 12
                else:
                    # 基础存款变动计算
                    if pension_contribution_paid < pension_years_remaining:
                        # 缴养老阶段存款变动 = max(基本每年基础开销 - 年收益, 0)
                        deposit_withdrawal = max(basic_annual_expense - annual_interest, 0)
                    elif not is_retired:
                        # 躺平阶段存款变动 = max(基本每年基础开销 - 年收益, 0)
                        deposit_withdrawal = max(basic_annual_expense - annual_interest, 0)
                    else:
                        # 养老阶段存款变动 = max(基本每年基础开销 - 年收益 + 养老金领取, 0)
                        deposit_withdrawal = max(basic_annual_expense - annual_interest + current_pension, 0)
                    
                    # 确保存款变动不超过可用存款（年初余额 + 年收益）
                    max_available_deposit = year_start_balance + annual_interest
                    deposit_withdrawal = min(deposit_withdrawal, max_available_deposit)
                    
                    # 年可用收入 = 基本每年基础开销 + 存款变动 - 养老金缴纳 + 养老金领取
                    annual_available_income = basic_annual_expense + deposit_withdrawal - current_pension_contribution + current_pension
                    monthly_available = annual_available_income / 12
            
            # 工作阶段：显示每年收入 = WORK_YEAR_SAVE + WORK_STOCKW
            # 躺平阶段：显示 STOCK_ANNUAL - PENSION_ANNUAL_CONTRIBUTION
            # 退休阶段：显示 STOCK_ANNUAL + PENSION_ANNUAL
            if is_working:
                stock_or_pension = work_year_save + work_stock  # 工作阶段显示每年收入
            elif pension_contribution_paid < pension_years_remaining:
                stock_or_pension = - current_pension_contribution  # 躺平阶段显示缴纳金额
            elif is_retired:
                stock_or_pension = current_pension  # 退休后显示养老金
            else:
                stock_or_pension = 0
            
            # 计算年末余额
            # 工作阶段：余额 = 年初余额 + 年收益 + 工作收入 - 存款变动 - 养老金缴纳
            # 非工作阶段：余额 = 年初余额 + 年收益 - 存款变动 - 养老金缴纳
            # 股票的钱不会被加在余额里，因为股票没有利息
            if is_working:
                end_balance = year_start_balance + annual_interest + work_income - deposit_withdrawal - current_pension_contribution
                # 工作阶段的股票增加到股票余额中，不影响存款余额
                stock_remaining += work_stock_add
            else:
                end_balance = year_start_balance + annual_interest - deposit_withdrawal - current_pension_contribution
            
            # 确定养老花销显示
            # 缴养老阶段：显示负数（支出）
            # 养老阶段：显示正数（收入）
            if pension_contribution_paid < pension_years_remaining:
                pension_expense = -current_pension_contribution  # 缴养老阶段显示负数
            else:
                pension_expense = current_pension  # 养老阶段显示正数
            
            phase = "养老" if is_retired else ("工作" if is_working else "躺平")
            
            # 确定阶段显示（添加养老金状态）
            if is_working:
                phase_display = f"工作({work_years_already + year + 1}年)"  # 工作阶段从已经工作的年限+1开始递增
            elif pension_contribution_paid < pension_years_remaining:
                phase_display = f"缴养老({pension_years_remaining - pension_contribution_paid}年)"
            else:
                phase_display = phase
        
        # 添加数据到表格（无论是否为最终结算点）
        if is_final_year:
            table_data.append([
                age,
                phase_display,
                f"{year_start_balance:>15,.0f}",
                f"{annual_interest:>15,.0f}",
                f"{0:>15,.0f}",  # 最终年份无工资
                f"{0:>15,.0f}",  # 最终年份无养老花销
                f"{deposit_withdrawal:>15,.0f}",
                f"{annual_available_income:>15,.0f}",
                f"{0:>15,.0f}",  # 最终年份无月可用
                f"{end_balance:>15,.0f}"
            ])
        else:
            table_data.append([
                age,
                phase_display,
                f"{year_start_balance:>15,.0f}",
                f"{annual_interest:>15,.0f}",
                f"{work_income:>15,.0f}",  # 工资
                f"{pension_expense:>15,.0f}",  # 养老花销（缴养老为负数，养老为正数）
                f"{deposit_withdrawal:>15,.0f}",
                f"{annual_available_income:>15,.0f}",
                f"{monthly_available:>15,.0f}",
                f"{end_balance:>15,.0f}"
            ])
        
        balance = end_balance
    
    headers = [
        "年龄",
        "阶段",
        "年初余额(元)",
        "年收益(元)",
        "工资(元)",
        "养老花销(元)",
        "存款变动(元)",
        "年可用(元)",
        "月可用(元)",
        "年末余额(元)"
    ]
    
    return table_data, headers, {
        'pension_years_remaining': pension_years_remaining,
        'pension_contribution': pension_contribution,
        'total_pension_contribution': total_pension_contribution,
        'age_to_qualify': age_to_qualify
    }

if __name__ == "__main__":
    # ==================== 配置参数 ====================
    # 当前工作信息
    MY_AGE = 26                                          # 当前年龄 (岁)
    WORK_YEARS = 1                                       # 当前工作年限 (年)
    WORK_YEAR_SAVE = 668000                              # 每年工作存款 (元)
    WORK_STOCK = 100 * 200 * 7                           # 每年工作股票 (元)
    WORK_HOUSE_MONEY = 11634                             # 每年双边公积金（元）
    NOW_MONEY = 1222237                                  # 当前资金 (元)
    NOW_HOUSE_MONEY = 220000                             # 当前双边公积金 (元)
    NOW_STOCK = 163 * 200 * 7                            # 当前股票 (元)
    PLAN_WORK_YEARS = 5                                  # 计划工作年限 (年)
    
    # 开始躺平时存款配置
    ANNUAL_RATE = 1                             # 年收益率 (%)
    REMAINING_WORK_YEARS = PLAN_WORK_YEARS - WORK_YEARS  # 剩余工作年限 (年)
    LEI_AGE = MY_AGE + PLAN_WORK_YEARS - WORK_YEARS     # 躺平年龄 (岁，四舍五入)
    # 计算工作年限
    work_years = LEI_AGE - MY_AGE
    PRINCIPAL = NOW_MONEY  # 初始存款金额 (元)
    STOCK_TOTAL = NOW_STOCK + (WORK_STOCK * REMAINING_WORK_YEARS)    # 股票总额 (元)，包括当前股票和工作期间的股票积累
    RETIREMENT_AGE = 60                         # 退休年龄 (岁)
    TARGET_AGE = 90                             # 计划寿命 (岁)
    
    # 股票每年预计取出
    STOCK_ANNUAL = 30000                        # 股票每年可领 (元)
    
    # 退休工资
    PENSION_ANNUAL = 41376                      # 养老金每年 (元)

    # 养老金缴纳配置
    PENSION_TOTAL_YEARS = 20                    # 需要交满的总年限 (年)
    PENSION_PAID_YEARS = PLAN_WORK_YEARS        # 已缴纳的年限 (年) = 计划工作年限
    PENSION_ANNUAL_CONTRIBUTION = 36000         # 后续每年缴纳金额 (元)

    # ==================== 导出配置 ====================
    EXPORT_ENABLED = False                       # 是否导出结果文档 (True/False)
    EXPORT_FORMAT = "md"                        # 导出格式: "txt" 或 "md"
    EXPORT_PATH = f"financial_plan_{PLAN_WORK_YEARS}"  # 导出文件名
    # =================================================
    
    lying_flat_years = RETIREMENT_AGE - LEI_AGE
    retirement_years = TARGET_AGE - RETIREMENT_AGE
    total_years = TARGET_AGE - LEI_AGE
    
    print("\n" + "=" * 70)
    print("\t\t存款规划计算器")
    # 计算不工作年限
    non_work_years = TARGET_AGE - LEI_AGE
    
    # 计算预计未来工资收入
    future_salary_income = WORK_YEAR_SAVE * REMAINING_WORK_YEARS
    
    # 计算预计未来股票收入
    future_stock_income = STOCK_ANNUAL * REMAINING_WORK_YEARS
    
    # 计算预计未来公积金收入
    future_house_money = WORK_HOUSE_MONEY * REMAINING_WORK_YEARS
    
    # 计算总养老金缴纳
    total_pension_contribution = PENSION_ANNUAL_CONTRIBUTION * (PENSION_TOTAL_YEARS - PENSION_PAID_YEARS)
    
    # 计算基本每年基础开销
    # 总资金 = 初始存款 + 初始股票 + 初始公积金 + 未来工资收入 + 未来股票收入 + 未来公积金收入 - 养老金缴纳
    # 基本每年基础开销 = 总资金 / 不工作年限
    total_funds = NOW_MONEY + NOW_STOCK + NOW_HOUSE_MONEY + future_salary_income + future_stock_income + future_house_money - total_pension_contribution
    print(f"预计总资金: {total_funds:,.0f}元")
    basic_annual_expense = total_funds / non_work_years if non_work_years > 0 else 0
    
    print(f"基本每年基础开销: {basic_annual_expense:,.0f}元")
    
    result = generate_savings_table(PRINCIPAL, ANNUAL_RATE, MY_AGE, LEI_AGE, RETIREMENT_AGE, TARGET_AGE,
                                   STOCK_TOTAL, STOCK_ANNUAL, PENSION_ANNUAL,
                                   PENSION_TOTAL_YEARS, PENSION_PAID_YEARS, PENSION_ANNUAL_CONTRIBUTION,
                                   WORK_YEAR_SAVE, WORK_STOCK, WORK_YEARS,
                                   WORK_HOUSE_MONEY, NOW_HOUSE_MONEY, basic_annual_expense)
    
    if result is None:
        print("❌ 无法计算，请检查输入参数")
        exit()
    
    table_data, headers, pension_info = result
    pension_years_remaining = pension_info['pension_years_remaining']
    pension_contribution = pension_info['pension_contribution']
    total_pension_contribution = pension_info['total_pension_contribution']
    age_to_qualify = pension_info['age_to_qualify']
    
    print("\n" + tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
    
    work_years = PLAN_WORK_YEARS
    lying_flat_years = RETIREMENT_AGE - LEI_AGE
    retirement_years = TARGET_AGE - RETIREMENT_AGE
    total_years = work_years + lying_flat_years + retirement_years
    
    print("\n" + "=" * 70)
    print("\t\t规划汇总")
    print("=" * 70)
    print(f"工作年数:\t{work_years} 年 ({MY_AGE}岁 -> {MY_AGE + work_years - 1}岁)")
    print(f"躺平年数:\t{lying_flat_years} 年 ({LEI_AGE}岁 -> {RETIREMENT_AGE - 1}岁)")
    print(f"养老年数:\t{retirement_years} 年 ({RETIREMENT_AGE}岁 -> {TARGET_AGE - 1}岁)")
    print(f"总年数:\t{total_years} 年 ({MY_AGE}岁 -> {TARGET_AGE - 1}岁)")
    print("─" * 70)
    print("资金来源:")
    print(f"\t初始存款:\t{NOW_MONEY:,}元")
    print(f"\t股票总额:\t{STOCK_TOTAL:,}元")
    print(f"\t初始双边公积金:\t{NOW_HOUSE_MONEY:,}元")
    print(f"\t养老金:\t{PENSION_ANNUAL:,}元 /年 x {retirement_years}年 \t退休后({RETIREMENT_AGE}岁)开始领取养老金")
    print(f"\t预计未来工资收入:\t{WORK_YEAR_SAVE:,}元 /年 x {work_years}年")
    print(f"\t预计未来股票收入:\t{WORK_STOCK:,}元 /年 x {work_years}年")
    print(f"\t预计未来公积金收入:\t{WORK_HOUSE_MONEY:,}元 /年 x {work_years}年")
    print("─" * 70)
    print("资金固定开销:")
    if pension_years_remaining > 0:
        print(f"\t养老金缴纳:{pension_contribution:,}元 /年 x {pension_years_remaining}年 = {total_pension_contribution:,}元")
    print("─" * 70)
    print("计算公式:")
    print(f"\t基本每年基础开销：（初始存款 + 股票余额 + 初始双边公积金 + 预计未来工资收入 + 预计未来股票收入 + 预计未来公积金收入 - 养老金缴纳）/ （不工作年限） = {basic_annual_expense:,.0f}元")
    print(f"\t缴养老阶段存款变动 = max(基本每年基础开销 - 年收益, 0)")
    print(f"\t躺平阶段存款变动 = max(基本每年基础开销 - 年收益, 0)")
    print(f"\t养老阶段存款变动 = max(基本每年基础开销 - 年收益 + 养老金领取, 0)")
    print(f"\t月可用收入 = 年可用收入 / 12 (每年不同)")
    print(f"\t确保存款在{TARGET_AGE}岁时刚好耗尽")
    print("─" * 70)
    
    if work_years > 0:
        print("工作阶段 ({}岁-{}岁):".format(MY_AGE, MY_AGE + work_years - 1))
        print(f"\t每年存款:{WORK_YEAR_SAVE:,}元 /年")
        print(f"\t每年股票:{WORK_STOCK:,}元 /年")
        print(f"\t股票/养老: 0")
        print(f"\t存款变动: 0")
        print(f"\t年可用: 0")
    print("─" * 70)
    
    if pension_years_remaining > 0:
        age_to_qualify = LEI_AGE + pension_years_remaining
        if age_to_qualify < RETIREMENT_AGE:
            print(f"养老金缴纳阶段 ({LEI_AGE}-{age_to_qualify}岁):")
            print(f"\t养老金缴纳:{pension_contribution:,}元 /年")
            print(f"\t存款变动:max(基本每年基础开销 - 年收益, 0)")
        print("─" * 70)
    print(f"躺平阶段 ({LEI_AGE}-{RETIREMENT_AGE-1}岁):")
    print(f"\t(养老金{RETIREMENT_AGE}岁后开始领取)")
    print(f"\t存款变动:max(基本每年基础开销 - 年收益, 0)")
    print("─" * 70)
    print(f"养老阶段 ({RETIREMENT_AGE}-{TARGET_AGE-1}岁):")
    print(f"\t养老金: {PENSION_ANNUAL:,}元 /年")
    print(f"\t存款变动:max(基本每年基础开销 - 年收益 + 养老金领取, 0)")
    print("=" * 70)


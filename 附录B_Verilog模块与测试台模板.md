# 附录 B　Verilog 模块与测试台模板

这个附录把全书反复用到的 Verilog 写法集中起来，供查漏和复用。每个模板都来自正文里已经跑通的代码，放在 `code/verilog/appendix_b/`，三组测试台全部通过。写代码时不必从头想起，来这里找一块改改就能用。

模板分两类。一类是电路模块，包括带使能的触发器、寄存器堆、ALU、指令存储器；另一类是测试台的骨架，包括时钟复位、检查任务和结束条件。最后列几条实践中容易踩的坑。

## B.1 带使能的 D 触发器

### 要解决什么问题

处理器里到处是"到时钟沿才更新"的状态：PC、流水线寄存器、CSR。它们的行为都一样：复位时清零，时钟沿到来时，若使能打开就存入新值，否则保持原值。把这个行为写成一个模块，以后不用每次重来。

### 接口怎么来

先看存状态需要什么。时钟和复位是时序逻辑的标配，少一个都不行。

```verilog
    input  wire       clk,
    input  wire       rst_n,
```

复位信号用低电平有效，写成 `rst_n`，这是全书统一的约定。

再看数据这一侧。要有个数据输入，还要有个信号决定"这一拍到底存不存"。

```verilog
    input  wire       en,
    input  wire       d,
```

最后是要被驱动的输出。它在本拍里保持旧值，所以声明成 `reg`。

```verilog
    output reg        q
```

接口就齐了。

### 实现

时序逻辑写在 `always @(posedge clk)` 里，用非阻塞赋值 `<=`。复位和使能构成两级判断：复位优先，其次看使能。

```verilog
    always @(posedge clk) begin
        if (!rst_n)
            q <= 1'b0;
        else if (en)
            q <= d;
    end
```

这里没有 `else` 分支。`en` 为 0 时什么也不做，`q` 自然保持原值，这正是我们要的效果。变量名省略赋值会让综合工具推断出触发器，仿真器也会保持旧值。

完整代码在 `code/verilog/appendix_b/dff_en.v`：

```verilog
module dff_en (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       en,
    input  wire       d,
    output reg        q
);

    always @(posedge clk) begin
        if (!rst_n)
            q <= 1'b0;
        else if (en)
            q <= d;
    end

endmodule
```

这个模块在第 4 章第一次出现，第 9 章的流水线寄存器用的也是同一套写法，只是数据从 1 位加宽到几十位，把 `d` 和 `q` 改成总线即可。

## B.2 寄存器堆

### 要解决什么问题

RV32I 程序员眼里的 32 个通用寄存器，在硬件里是一个 32 项、每项 32 位的存储阵列。它有两个读端口和一个写端口，因为一条典型指令要读两个源操作数、写一个结果。

### 接口怎么来

存状态要有时钟和复位，这两样先引出来。

```verilog
    input  wire        clk,
    input  wire        rst_n,
```

再看读端口。给出寄存器号，返回对应的值。一条指令通常要读两个源操作数，所以需要两组输入输出。

```verilog
    input  wire [4:0]  rs1,
    input  wire [4:0]  rs2,
```

写端口除了寄存器号和数据，还要一个使能信号。没有它，每条指令都会往某个寄存器里写，程序立刻乱套。

```verilog
    input  wire [4:0]  rd,
    input  wire        we,
    input  wire [31:0] wdata,
```

最后是两路读出的数据。

```verilog
    output wire [31:0] rdata1,
    output wire [31:0] rdata2
```

接口就齐了。
### 实现里要注意什么

第一件事是 `x0`。规范规定它恒为零，所以写端口必须挡住 `rd == 0`，读端口遇到 `rs1 == 0` 或 `rs2 == 0` 也要直接返回零，不去读存储器。少一个判断，`x0` 就不再是零了。

第二件事是复位。数组不能在声明时清零，得在复位分支里用循环逐项写。

```verilog
    reg [31:0] regs [0:31];
    integer i;

    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 32; i = i + 1)
                regs[i] <= 32'b0;
        end else if (we && (rd != 5'd0)) begin
            regs[rd] <= wdata;
        end
    end
```

读端口用连续赋值，两个判断分别处理两个端口：

```verilog
    assign rdata1 = (rs1 == 5'd0) ? 32'b0 : regs[rs1];
    assign rdata2 = (rs2 == 5'd0) ? 32'b0 : regs[rs2];
```

完整代码在 `code/verilog/appendix_b/regfile.v`：

```verilog
module regfile (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [4:0]  rs1,
    input  wire [4:0]  rs2,
    input  wire [4:0]  rd,
    input  wire        we,
    input  wire [31:0] wdata,
    output wire [31:0] rdata1,
    output wire [31:0] rdata2
);

    reg [31:0] regs [0:31];
    integer i;

    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 32; i = i + 1)
                regs[i] <= 32'b0;
        end else if (we && (rd != 5'd0)) begin
            regs[rd] <= wdata;
        end
    end

    assign rdata1 = (rs1 == 5'd0) ? 32'b0 : regs[rs1];
    assign rdata2 = (rs2 == 5'd0) ? 32'b0 : regs[rs2];

endmodule
```

这个版本是第 5 章的写法。第 10 章为了解决"距离三条指令"的数据相关，在它内部加了一条写直通，把本拍要写回的数据直接旁路到读端口；那是针对流水线问题的改动，基础的寄存器堆保持这个样子就够了。

## B.3 组合逻辑块的标准写法

### 要解决什么问题

ALU、译码器、立即数生成这些电路没有状态，输入一变输出就该跟着变。这种电路叫组合逻辑，写法和时序逻辑完全不同，混用会导致仿真出波形、综合出锁存器这类怪问题。

### 两条规矩

组合逻辑用 `always @(*)`，里面用阻塞赋值 `=`：

```verilog
    always @(*) begin
        case (alu_op)
            ALU_ADD: result = add_result;
            ALU_SUB: result = add_result;
            ALU_AND: result = a & b;
            ALU_OR:  result = a | b;
            ALU_XOR: result = a ^ b;
            ALU_SLT: result = (a[31] != b[31]) ? {31'b0, a[31]} : {31'b0, (a < b)};
            ALU_SLL: result = a << b[4:0];
            ALU_SRL: result = a >> b[4:0];
            default: result = 32'b0;
        endcase
    end
```

这里有三点值得留意。`always @(*)` 让仿真器自动敏感于块里读到的所有信号，不必手工列敏感表；`case` 里用阻塞赋值 `=`，表示立即算出结果；最后一定要有 `default`，否则某些输入组合下 `result` 会保持旧值，综合工具就会推断出锁存器。

还有一条：组合逻辑块里赋值的输出要声明成 `reg`，哪怕它在硬件里只是一根线。这是 Verilog 语法的要求，`reg` 在这里的意思不是"触发器"，而是"过程块里被赋值的变量"。ALU 的端口声明就体现了这一点：

```verilog
module alu (
    input  wire [31:0] a,
    input  wire [31:0] b,
    input  wire [3:0]  alu_op,
    output reg  [31:0] result,
    output wire        zero
);
```

`result` 在 `always` 块里赋值，声明成 `reg`；`zero` 用 `assign` 连续赋值，声明成 `wire`。

### 加法器与子模块

ALU 把 32 位加法交给独立的 `adder_32`，后者用 `generate` 循环把 32 个全加器串起来。这种写法比手抄 32 行短得多，改位宽也只需改一个数字。

```verilog
    genvar i;
    generate
        for (i = 0; i < 32; i = i + 1) begin : g_bit
            if (i == 0) begin : g_first
                full_adder u_fa (
                    .a    (a[0]),
                    .b    (b[0]),
                    .cin  (cin),
                    .sum  (sum[0]),
                    .cout (carry[0])
                );
            end else begin : g_rest
                full_adder u_fa (
                    .a    (a[i]),
                    .b    (b[i]),
                    .cin  (carry[i-1]),
                    .sum  (sum[i]),
                    .cout (carry[i])
                );
            end
        end
    endgenerate
```

最低位没有前一级进位，所以单独用一个 `if` 分支处理。实例化时用 `.a(a[i])` 这样的具名连接，比按顺序连可靠得多：端口顺序改了也不会连错。

附录目录里的 `alu.v`、`adder_32.v`、`full_adder.v`、`half_adder.v` 四个文件构成完整的一条链，配合 `tb_alu.v` 可以独立跑通。

## B.4 立即数生成的写法

### 要解决什么问题

RV32I 的立即数被打散在不同位置，译码时要按指令格式把它们拼回 32 位。这段代码在第 8 章第一次出现，后面各章的核都沿用。

### 实现

先把五个字段提取出来，每一条对应一种格式：

```verilog
    wire [31:0] imm_i = {{20{instr[31]}}, instr[31:20]};
    wire [31:0] imm_s = {{20{instr[31]}}, instr[31:25], instr[11:7]};
    wire [31:0] imm_b = {{19{instr[31]}}, instr[31], instr[7], instr[30:25], instr[11:8], 1'b0};
    wire [31:0] imm_u = {instr[31:12], 12'b0};
    wire [31:0] imm_j = {{11{instr[31]}}, instr[31], instr[19:12], instr[20], instr[30:21], 1'b0};
```

`{{20{instr[31]}}, ...}` 是符号扩展：把最高位复制 20 遍，接在原来的 12 位前面，凑成 32 位。B 型和 J 型的最低位固定为 0，因为跳转目标必须 2 字节对齐。U 型不做符号扩展，高 20 位直接放到结果高位，低 12 位补零。

拼好之后按操作码挑一个：

```verilog
    reg [31:0] imm_r;
    always @(*) begin
        case (opcode)
```

这段的完整代码在 `code/verilog/appendix_b/control.v`。注意它是一个大的组合块，末尾同样要有 `default`，保证任何操作码下都有确定输出。

## B.5 用 $readmemh 装载程序

### 要解决什么问题

处理器要跑程序，得先把机器码放进指令存储器。写死在代码里太笨，应该从一个 hex 文件读进来。

### 实现

```verilog
    reg [31:0] mem [0:DEPTH-1];

    initial begin
        $readmemh("code.hex", mem);
    end
```

`$readmemh` 是仿真任务，在仿真开始时把文件里的十六进制数逐行填进数组。文件每行一个 32 位字，小端序的程序要用 `tools/bin_to_hex.py` 之类的脚本先转成这个格式。

地址译码部分要减掉存储器的基地址，再用字地址索引：

```verilog
    wire [31:0] offset = addr - BASE;
    wire [IDX_W-1:0] idx = offset[IDX_W+1:2];

    always @(*) begin
        if (addr >= BASE && offset < DEPTH * 4)
            instr = mem[idx];
        else
            instr = 32'h00000013;
    end
```

`offset[IDX_W+1:2]` 是右移两位，把字节地址变成字地址。越界访问返回 `0x00000013`，也就是 `nop`，这样程序跑飞时不会取到非法指令，便于观察。完整代码在 `code/verilog/appendix_b/imem.v`。

## B.6 测试台骨架

### 要解决什么问题

写好了模块，得有个地方给它加激励、检查输出、报告结果。测试台不参与综合，写法可以随意，但有几样东西几乎每次都要用：时钟、复位、检查任务和结束条件。

### 时钟与复位

方波时钟用一条 `always` 语句产生：

```verilog
    always #5 clk = ~clk;
```

这行产生周期 10 个时间单位的时钟。`timescale` 声明决定单位，全书统一用 1 ns / 1 ps，所以周期是 10 ns。

复位要在 `initial` 块里先拉低、过一小段时间再拉高。先给一段低电平，让所有触发器进入确定状态：

```verilog
    initial begin
        clk = 0;
        rst_n = 0;
        en = 0;
        d = 0;
        errors = 0;

        #12;
        check(1'b0, "reset clears q");
        rst_n = 1;
```

### 检查任务

每次检查都要打印通过还是失败，失败时累计错误数。把它写成一个 `task`，后面就不用重复：

```verilog
    task check;
        input          expected;
        input [1023:0] text;
        begin
            if (q !== expected) begin
                $display("FAIL: %0t  %s  (q=%b, expected=%b)", $time, text, q, expected);
                errors = errors + 1;
            end else begin
                $display("PASS: %0t  %s", $time, text);
            end
        end
    endtask
```

消息参数写成 `[1023:0]` 而不是常见的 `[255:0]`，是为了放下长消息。位宽不够时字符串会被悄悄截断，排查起来很费时间。比较用 `!==` 而不是 `!=`，这样 `x` 和 `z` 也会被判为失败，不会蒙混过关。

### 结束条件

测试跑完要给出明确结论并停下：

```verilog
        $display("--------------------------------");
        if (errors == 0)
            $display("ALL TESTS PASSED");
        else
            $display("%0d TESTS FAILED", errors);
        $finish;
    end
```

完整的 `tb_dff_en.v` 有 7 项检查，覆盖复位、使能开启、使能关闭和数据变化，可以直接拿去改。目录里的 `tb_regfile.v` 和 `tb_alu.v` 是稍微复杂一点的例子。

运行方法：

```bash
iverilog -g2012 -o sim.out dff_en.v tb_dff_en.v
vvp sim.out
```

三条测试台命令分别为：

```bash
iverilog -g2012 -o sim.out dff_en.v tb_dff_en.v && vvp sim.out
iverilog -g2012 -o sim.out regfile.v tb_regfile.v && vvp sim.out
iverilog -g2012 -o sim.out alu.v adder_32.v full_adder.v half_adder.v tb_alu.v && vvp sim.out
```

三组都打印 `ALL TESTS PASSED` 才算环境正常。

## B.7 几条容易踩的坑

**保留字不能用。** `table`、`expect` 是 Verilog 保留字，拿去当信号名会直接报错。本书把标记存储器叫 `tag_ram`，把预期地址叫 `exp_addr`，就是为了绕开它们。

**数组上界要用常量。** Icarus Verilog 不接受数组声明里直接写参数表达式，得先转成 `localparam`。模板目录里的 `fifo.v` 是个通用同步队列，开头就这么写：

```verilog
    localparam PTR_W    = $clog2(DEPTH) + 1;  // 下标位数多留 1 位判满
    localparam DEPTH_M1 = DEPTH - 1;  // iverilog 不接受数组上界直接写参数表达式
```

**多一位指针的队列，索引只能用低位。** 深度 8 的队列，指针要 4 位才能判满，但数组下标只有 3 位。写满时完整指针会走到 8，用它索引就越界读出 `x`。正确写法是 `mem[tail[PTR_W-2:0]]`。

**判满要用当前 tail。** 用 `tail + 1` 判断会让队列深度平白少一格。判据是最高位不同、其余位相同，而且两边都取当前值。

**复位沿要有明确跳变。** 未知态到 0 在 Icarus 里不一定触发 `negedge rst_n`。测试台里先拉高再拉低，给出确定的下降沿，比只写初值 0 可靠。

**组合逻辑的 `case` 要有 `default`。** 少一个分支，综合工具就会推断出锁存器，仿真时表现为输出莫名保持旧值。

这些坑大多在正文各章里踩过一次，写在这里省得再踩第二遍。模板本身不复杂，真正要留心的是这些细节。

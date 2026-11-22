`timescale 1ns/1ps

module tb_core;

    reg        clk   = 1'b0;
    reg        rst_n = 1'b0;
    reg  [7:0] switch_i = 8'h5a;
    reg  [7:0] rx_i     = 8'h7a;
    reg        rx_valid_i = 1'b1;
    wire [7:0] led_o;
    wire [7:0] tx_o;
    wire       tx_valid_o;
    wire [31:0] pc;

    core uut (
        .clk        (clk),
        .rst_n      (rst_n),
        .switch_i   (switch_i),
        .rx_i       (rx_i),
        .rx_valid_i (rx_valid_i),
        .led_o      (led_o),
        .tx_o       (tx_o),
        .tx_valid_o (tx_valid_o),
        .pc_out     (pc)
    );

    always #5 clk = ~clk;

    integer errors = 0;
    reg [1023:0] msg;

    task check;
        input [31:0] got;
        input [31:0] want;
        input [1023:0] label;
        begin
            if (got !== want) begin
                $display("FAIL %0t: %s  got=0x%08h  want=0x%08h", $time, label, got, want);
                errors = errors + 1;
            end else begin
                $display("PASS %0t: %s  = 0x%08h", $time, label, got);
            end
        end
    endtask

    // 记录串口发出的字节序列
    reg [7:0] tx_log [0:15];
    integer tx_cnt = 0;
    always @(posedge clk) begin
        if (rst_n && tx_valid_o) begin
            tx_log[tx_cnt] <= tx_o;
            tx_cnt = tx_cnt + 1;
        end
    end

    initial begin
        #12;
        check(pc, 32'h00400000, "reset pc");
        rst_n = 1'b1;

        // 按时钟沿推进，每条指令占用一拍
        @(posedge clk); #1;  // 1: lui x1
        check(uut.u_regfile.regs[1], 32'hffff0000, "peripheral base in x1");

        repeat (3) @(posedge clk); #1;  // 4: sw 写 LED
        check(led_o, 32'h000000a5, "LED pattern written");

        repeat (2) @(posedge clk); #1;  // 6: lw 读开关
        check(uut.u_regfile.regs[5], 32'h0000005a, "switch read into x5");

        repeat (6) @(posedge clk); #1;  // 12: 两次串口发送已完成
        check(tx_log[0], 32'h00000048, "first UART byte H");
        check(tx_log[1], 32'h00000069, "second UART byte i");

        repeat (1) @(posedge clk); #1;  // 13: lw 读 UART 状态
        check(uut.u_regfile.regs[10], 32'h00000021, "UART status THRE|DR");

        repeat (1) @(posedge clk); #1;  // 14: lw 读定时器
        if (uut.u_regfile.regs[11] > 0)
            $display("PASS %0t: timer counting = %0d", $time, uut.u_regfile.regs[11]);
        else begin
            $display("FAIL %0t: timer did not count", $time);
            errors = errors + 1;
        end

        repeat (1) @(posedge clk); #1;  // 15: lw 读 UART 接收数据
        check(uut.u_regfile.regs[12], 32'h0000007a, "UART rx byte into x12");

        if (errors == 0)
            $display("ALL TESTS PASSED");
        else
            $display("%d TESTS FAILED", errors);
        $finish;
    end

endmodule

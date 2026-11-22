`timescale 1ns/1ps

module tb_core;

    reg        clk   = 1'b0;
    reg        rst_n = 1'b0;
    wire [31:0] pc;

    core uut (
        .clk    (clk),
        .rst_n  (rst_n),
        .pc_out (pc)
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

    // 等待某个寄存器变成期望值，最多等 200 个周期
    task wait_reg;
        input [4:0]  idx;
        input [31:0] want;
        input [1023:0] label;
        integer n;
        begin
            n = 0;
            while (uut.u_regfile.regs[idx] !== want && n < 200) begin
                @(posedge clk);
                n = n + 1;
            end
            if (uut.u_regfile.regs[idx] !== want) begin
                $display("FAIL %0t: %s timeout, got=0x%08h want=0x%08h",
                         $time, label, uut.u_regfile.regs[idx], want);
                errors = errors + 1;
            end else begin
                $display("PASS %0t: %s  = 0x%08h", $time, label, want);
            end
        end
    endtask

    initial begin
        #12;
        rst_n = 1'b1;

        wait_reg(5'd1, 32'd7,           "x1 last write wins");
        wait_reg(5'd2, 32'd8,           "x2 from EX/MEM forwarding");
        wait_reg(5'd3, 32'd15,          "x3 both operands forwarded");
        wait_reg(5'd4, 32'd9,           "x4 before store");
        check({uut.u_dmem.mem[3], uut.u_dmem.mem[2], uut.u_dmem.mem[1], uut.u_dmem.mem[0]},
              32'd9, "dmem word after sw with forwarding");
        wait_reg(5'd5, 32'd9,           "x5 after lw");
        wait_reg(5'd6, 32'd10,          "x6 after load-use stall");
        wait_reg(5'd7, 32'd4,           "x7");
        wait_reg(5'd8, 32'd42,          "x8 from taken branch target");
        wait_reg(5'd9, 32'd55,          "x9 from not-taken path");
        wait_reg(5'd11, 32'h00400054,   "x11 link from jal at 0x50");
        wait_reg(5'd14, 32'h00400058,   "x14 link from jalr");

        // 被冲刷的指令不能写寄存器
        check(uut.u_regfile.regs[12], 32'd0, "x12 from flushed instruction stays 0");
        check(uut.u_regfile.regs[13], 32'd0, "x13 from flushed instruction stays 0");

        // jalr 的目标写进 pc，确认程序确实跳到了 0x54 附近
        // 五级流水线里跳转在 EX 级才定下来，取指已经多走了两拍，
        // 所以稳定后 pc 会在 0x54/0x58/0x5c 之间循环，都是自环指令
        begin
            reg seen_target;
            integer k;
            seen_target = 1'b0;
            for (k = 0; k < 30; k = k + 1) begin
                @(posedge clk);
                if ((pc >= 32'h00400054) && (pc <= 32'h0040005c))
                    seen_target = 1'b1;
            end
            check({31'b0, seen_target}, 32'd1, "pc loops in jalr target region");
        end

        if (errors == 0)
            $display("ALL TESTS PASSED");
        else
            $display("%d TESTS FAILED", errors);
        $finish;
    end

endmodule

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

    integer      errors = 0;
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

    initial begin
        #12;
        check(uut.u_regfile.regs[1], 32'd0, "x1 still zero right after reset");
        rst_n = 1'b1;

        // 五级流水线：指令写回比单周期晚 4 拍，检查点相应后移
        #53;
        check(uut.u_regfile.regs[1], 32'd5, "x1 after addi (5-stage latency)");

        #10;
        check(uut.u_regfile.regs[2], 32'd3, "x2 after addi");

        #40;
        check(uut.u_regfile.regs[3], 32'd8, "x3 after add (NOP-separated)");

        #10;
        check(uut.u_regfile.regs[4], 32'h10000000, "x4 after lui");

        #30;
        check({uut.u_dmem.mem[3], uut.u_dmem.mem[2], uut.u_dmem.mem[1], uut.u_dmem.mem[0]},
              32'd8, "dmem word after sw");

        #20;
        check(uut.u_regfile.regs[5], 32'd8, "x5 after lw");

        #40;
        check(uut.u_regfile.regs[6], 32'd9, "x6 after addi from loaded value");

        #20;
        check(pc, 32'h00400040, "pc parked at self loop");

        if (errors == 0)
            $display("ALL TESTS PASSED");
        else
            $display("%d TESTS FAILED", errors);
        $finish;
    end

endmodule

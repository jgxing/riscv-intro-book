`timescale 1ns/1ps

module tb_core;

    reg         clk   = 1'b0;
    reg         rst_n = 1'b0;
    reg         irq   = 1'b0;
    wire [31:0] pc;

    core uut (
        .clk    (clk),
        .rst_n  (rst_n),
        .irq_i  (irq),
        .pc_out (pc)
    );

    localparam [31:0] BASE    = 32'h00400000;
    localparam [31:0] HANDLER = 32'h00400040;

    integer checks = 0;
    integer errors = 0;

    task check;
        input [31:0] got;
        input [31:0] exp;
        input [1023:0] msg;
        begin
            checks = checks + 1;
            if (got !== exp) begin
                errors = errors + 1;
                $display("FAIL %0d: %0s  got=%h  exp=%h", checks, msg, got, exp);
            end else begin
                $display("PASS %0d: %0s", checks, msg);
            end
        end
    endtask

    reg [31:0] caught_cause [0:3];
    reg [31:0] caught_epc   [0:3];
    reg [31:0] caught_tval  [0:3];
    integer trap_cnt = 0;
    reg was_handler = 1'b0;

    always @(posedge clk) begin
        if (rst_n) begin
            if ((pc == HANDLER) && !was_handler) begin
                if (trap_cnt < 4) begin
                    caught_cause[trap_cnt] = uut.mcause;
                    caught_epc[trap_cnt]   = uut.mepc;
                    caught_tval[trap_cnt]  = uut.mtval;
                end
                trap_cnt = trap_cnt + 1;
            end
            was_handler <= (pc == HANDLER);
        end else begin
            was_handler <= 1'b0;
        end
    end

    always @(posedge clk) begin
        if (rst_n && (pc == BASE + 32'h30)) irq <= 1'b1;
        if (rst_n && (pc == HANDLER))       irq <= 1'b0;
    end

    always #5 clk = ~clk;

    initial begin
        $display("=== chapter 11 trap test ===");
        #10 rst_n = 1'b1;
        wait (trap_cnt >= 4);
        repeat (40) @(posedge clk);
        irq = 1'b0;

        check(trap_cnt[31:0], 32'd4, "four traps caught");
        check(caught_cause[0], 32'd8, "ecall cause");
        check(caught_epc[0],   BASE + 32'h10, "ecall mepc points to itself");
        check(caught_cause[1], 32'd2, "illegal instruction cause");
        check(caught_epc[1],   BASE + 32'h18, "illegal mepc points to itself");
        check(caught_tval[1],  32'hffffffff, "illegal mtval holds the instruction");
        check(caught_cause[2], 32'd3, "ebreak cause");
        check(caught_epc[2],   BASE + 32'h20, "ebreak mepc points to itself");
        check(caught_cause[3], 32'h8000000b, "external interrupt cause");
        check(caught_epc[3],   BASE + 32'h38, "interrupt mepc points to next pc");

        check(uut.u_regfile.regs[1], 32'd10, "x1 after main program");
        check(uut.u_regfile.regs[2], 32'd15, "x2 after ecall return");
        check(uut.u_regfile.regs[3], 32'd33, "x3 after illegal return");
        check(uut.u_regfile.regs[4], 32'd2048, "x4 after ebreak return");
        check(uut.u_regfile.regs[5], 32'd55, "x5 before interrupt");
        check(uut.u_regfile.regs[6], 32'd66, "x6 after interrupt return");

        check(uut.mtvec, HANDLER, "mtvec holds handler address");
        check(uut.mcause, 32'h8000000b, "mcause after last trap");
        check(uut.mstatus[3], 1'b1, "MIE restored by mret");
        check(uut.u_regfile.regs[10], 32'h8000000b, "csrrs reads mcause");
        check(uut.u_regfile.regs[11], BASE + 32'h38, "csrrs reads mepc");

        $display("checks=%0d errors=%0d", checks, errors);
        if (errors == 0)
            $display("ALL TESTS PASSED");
        else
            $display("TESTS FAILED");
        $finish;
    end

endmodule

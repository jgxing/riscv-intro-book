`timescale 1ns/1ps

module tb_regfile;

    reg         clk;
    reg         rst_n;
    reg  [4:0]  rs1;
    reg  [4:0]  rs2;
    reg  [4:0]  rd;
    reg         we;
    reg  [31:0] wdata;
    wire [31:0] rdata1;
    wire [31:0] rdata2;

    integer errors;

    regfile uut (
        .clk    (clk),
        .rst_n  (rst_n),
        .rs1    (rs1),
        .rs2    (rs2),
        .rd     (rd),
        .we     (we),
        .wdata  (wdata),
        .rdata1 (rdata1),
        .rdata2 (rdata2)
    );

    always #5 clk = ~clk;

    task check1;
        input [31:0]   expected;
        input [1023:0] text;
        begin
            if (rdata1 !== expected) begin
                $display("FAIL: %s  (rdata1=%h, expected=%h)", text, rdata1, expected);
                errors = errors + 1;
            end else begin
                $display("PASS: %s", text);
            end
        end
    endtask

    task check2;
        input [31:0]   expected;
        input [1023:0] text;
        begin
            if (rdata2 !== expected) begin
                $display("FAIL: %s  (rdata2=%h, expected=%h)", text, rdata2, expected);
                errors = errors + 1;
            end else begin
                $display("PASS: %s", text);
            end
        end
    endtask

    initial begin
        clk = 0;
        rst_n = 0;
        rs1 = 5'd0;
        rs2 = 5'd0;
        rd = 5'd0;
        we = 1'b0;
        wdata = 32'h0;
        errors = 0;

        #12;
        rs1 = 5'd5;
        rs2 = 5'd6;
        #1;
        check1(32'h0, "reset clears x5");
        check2(32'h0, "reset clears x6");
        rst_n = 1;

        #10;
        rd = 5'd5;
        we = 1'b1;
        wdata = 32'h12345678;
        #10;
        check1(32'h12345678, "write x5 and read on port 1");

        #2;
        rs2 = 5'd5;
        #1;
        check2(32'h12345678, "read x5 on port 2 at the same time");

        #2;
        rs1 = 5'd0;
        rd = 5'd0;
        wdata = 32'hDEADBEEF;
        #10;
        check1(32'h0, "writes to x0 are ignored");

        #2;
        rd = 5'd6;
        we = 1'b0;
        wdata = 32'hA5A5A5A5;
        #10;
        rs1 = 5'd6;
        #1;
        check1(32'h0, "we=0 keeps the old value");

        #2;
        we = 1'b1;
        #10;
        check1(32'hA5A5A5A5, "write x6 when we=1");

        $display("--------------------------------");
        if (errors == 0)
            $display("ALL TESTS PASSED");
        else
            $display("%0d TESTS FAILED", errors);
        $finish;
    end

endmodule

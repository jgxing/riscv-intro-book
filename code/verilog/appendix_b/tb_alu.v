`timescale 1ns/1ps

module tb_alu;

    reg  [31:0] a;
    reg  [31:0] b;
    reg  [3:0]  op;
    wire [31:0] result;
    wire        zero;

    integer errors;

    alu uut (
        .a      (a),
        .b      (b),
        .alu_op (op),
        .result (result),
        .zero   (zero)
    );

    task check32;
        input [31:0]    expected;
        input [1023:0]  text;
        begin
            if (result !== expected) begin
                $display("FAIL: %s  (result=%h, expected=%h)", text, result, expected);
                errors = errors + 1;
            end else begin
                $display("PASS: %s", text);
            end
        end
    endtask

    task check_bit;
        input           expected;
        input [1023:0]  text;
        begin
            if (zero !== expected) begin
                $display("FAIL: %s  (zero=%b, expected=%b)", text, zero, expected);
                errors = errors + 1;
            end else begin
                $display("PASS: %s", text);
            end
        end
    endtask

    initial begin
        errors = 0;

        a = 32'd10;      b = 32'd3;          op = 4'd0; #1;
        check32(32'd13, "ADD 10+3");

        op = 4'd1; #1;
        check32(32'd7,  "SUB 10-3");

        a = 32'd3;       b = 32'd10;         op = 4'd1; #1;
        check32(32'hFFFFFFF9, "SUB 3-10 wraps around");

        a = 32'hF0F0F0F0; b = 32'h0FF00FF0; op = 4'd2; #1;
        check32(32'h00F000F0, "AND");

        op = 4'd3; #1;
        check32(32'hFFF0FFF0, "OR");

        op = 4'd4; #1;
        check32(32'hFF00FF00, "XOR");

        a = 32'hFFFFFFFF; b = 32'd1;         op = 4'd5; #1;
        check32(32'd1, "SLT -1 < 1");

        a = 32'd1;        b = 32'hFFFFFFFF;  op = 4'd5; #1;
        check32(32'd0, "SLT 1 < -1 is false");

        a = 32'd5;        b = 32'd9;         op = 4'd5; #1;
        check32(32'd1, "SLT 5 < 9");

        a = 32'd1;        b = 32'd4;         op = 4'd6; #1;
        check32(32'd16, "SLL by 4");

        a = 32'h80000000; b = 32'd4;         op = 4'd7; #1;
        check32(32'h08000000, "SRL by 4");

        a = 32'd0;        b = 32'd0;         op = 4'd0; #1;
        check32(32'd0, "ADD 0+0 result");
        check_bit(1'b1, "zero flag set when result is 0");

        a = 32'd1;        b = 32'd1;         op = 4'd1; #1;
        check_bit(1'b1, "zero flag set after 1-1");

        b = 32'd2; #1;
        check_bit(1'b0, "zero flag clear after 1-2");

        $display("--------------------------------");
        if (errors == 0)
            $display("ALL TESTS PASSED");
        else
            $display("%0d TESTS FAILED", errors);
        $finish;
    end

endmodule

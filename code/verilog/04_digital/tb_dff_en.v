`timescale 1ns/1ps

module tb_dff_en;

    reg          clk;
    reg          rst_n;
    reg          en;
    reg          d;
    wire         q;

    integer      errors;

    dff_en uut (
        .clk   (clk),
        .rst_n (rst_n),
        .en    (en),
        .d     (d),
        .q     (q)
    );

    always #5 clk = ~clk;

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

    initial begin
        clk = 0;
        rst_n = 0;
        en = 0;
        d = 0;
        errors = 0;

        #12;
        check(1'b0, "reset clears q");
        rst_n = 1;

        #10;
        en = 1;
        d = 1;
        #10;
        check(1'b1, "en=1 loads d=1");

        #2;
        en = 0;
        d = 0;
        #10;
        check(1'b1, "en=0 holds the old value");

        #2;
        en = 1;
        d = 0;
        #10;
        check(1'b0, "en=1 loads d=0");

        #2;
        en = 0;
        d = 1;
        #10;
        check(1'b0, "en=0 ignores a changing d");

        #2;
        rst_n = 0;
        #10;
        check(1'b0, "reset again");

        #2;
        rst_n = 1;
        en = 1;
        d = 1;
        #10;
        check(1'b1, "loads again after reset release");

        $display("--------------------------------");
        if (errors == 0)
            $display("ALL TESTS PASSED");
        else
            $display("%0d TESTS FAILED", errors);
        $finish;
    end

endmodule
